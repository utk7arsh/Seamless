/**
 * Frontend-only script: push movie data to Snowflake or pull from Snowflake.
 * Uses SNOWFLAKE_* env vars (load from repo root .env).
 *
 * Usage (from frontend/):
 *   node scripts/snowflake-movies.cjs push   # store movies.json in Snowflake
 *   node scripts/snowflake-movies.cjs pull   # overwrite src/data/movies.json from Snowflake
 *   node scripts/snowflake-movies.cjs fetch  # print movies JSON to stdout (used by Vite /api/movies)
 */

const path = require("path");
const fs = require("fs");

// Load .env from repo root (parent of frontend/)
require("dotenv").config({ path: path.resolve(__dirname, "../../.env") });

const snowflake = require("snowflake-sdk");

const MOVIES_JSON_PATH = path.resolve(__dirname, "../src/data/movies.json");
const TABLE_NAME = "MOVIES";

function getConnectionOptions() {
  const account = process.env.SNOWFLAKE_ACCOUNT;
  const user = process.env.SNOWFLAKE_USER;
  const password = process.env.SNOWFLAKE_PASSWORD;
  const role = process.env.SNOWFLAKE_ROLE;
  const warehouse = process.env.SNOWFLAKE_WAREHOUSE;
  const database = process.env.SNOWFLAKE_DATABASE;
  const schema = process.env.SNOWFLAKE_SCHEMA;

  if (!account || !user || !password) {
    throw new Error(
      "Missing SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, or SNOWFLAKE_PASSWORD. Set them in the repo root .env."
    );
  }

  return {
    account,
    username: user,
    password,
    role: role || "SYSADMIN",
    warehouse: warehouse || "COMPUTE_WH",
    database: database || "SEAMLESS_DB",
    schema: schema || "PUBLIC",
  };
}

function connect() {
  return new Promise((resolve, reject) => {
    const opts = getConnectionOptions();
    const conn = snowflake.createConnection(opts);
    conn.connect((err) => {
      if (err) reject(err);
      else resolve(conn);
    });
  });
}

function execute(conn, sql, binds = []) {
  return new Promise((resolve, reject) => {
    conn.execute({
      sqlText: sql,
      binds: binds.length ? binds : undefined,
      complete: (err, stmt, rows) => {
        if (err) reject(err);
        else resolve(rows || []);
      },
    });
  });
}

function ensureTable(conn) {
  const sql = `
    CREATE OR REPLACE TABLE ${TABLE_NAME} (
      id VARCHAR(32) PRIMARY KEY,
      title VARCHAR(512),
      video_path VARCHAR(512),
      image_path VARCHAR(512),
      ad_timing NUMBER,
      ad_duration NUMBER,
      match_score NUMBER,
      rating VARCHAR(32),
      seasons NUMBER,
      description VARCHAR(2048),
      year NUMBER,
      updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
    )
  `;
  return execute(conn, sql);
}

async function push() {
  const raw = fs.readFileSync(MOVIES_JSON_PATH, "utf8");
  const movies = JSON.parse(raw);
  if (!Array.isArray(movies) || !movies.length) {
    throw new Error("movies.json must be a non-empty array");
  }

  const conn = await connect();
  try {
    await ensureTable(conn);
    for (const m of movies) {
      const sql = `
        MERGE INTO ${TABLE_NAME} AS t
        USING (SELECT ? AS id) AS s ON t.id = s.id
        WHEN MATCHED THEN UPDATE SET
          title = ?, video_path = ?, image_path = ?,
          ad_timing = ?, ad_duration = ?, match_score = ?,
          rating = ?, seasons = ?, description = ?, year = ?,
          updated_at = CURRENT_TIMESTAMP()
        WHEN NOT MATCHED THEN INSERT (id, title, video_path, image_path, ad_timing, ad_duration, match_score, rating, seasons, description, year)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `;
      const binds = [
        m.id,
        m.title,
        m.video_path || "",
        m.image_path || "",
        m.ad_timing ?? 0,
        m.ad_duration ?? 0,
        m.match ?? null,
        m.rating || null,
        m.seasons ?? null,
        m.description || null,
        m.year ?? null,
        m.id,
        m.title,
        m.video_path || "",
        m.image_path || "",
        m.ad_timing ?? 0,
        m.ad_duration ?? 0,
        m.match ?? null,
        m.rating || null,
        m.seasons ?? null,
        m.description || null,
        m.year ?? null,
      ];
      await execute(conn, sql, binds);
    }
    console.log(`Pushed ${movies.length} movies to Snowflake table ${TABLE_NAME}.`);
  } finally {
    conn.destroy((err) => {
      if (err) console.error("Connection close error:", err);
    });
  }
}

function rowsToMovies(rows) {
  return rows.map((r) => ({
    id: r.ID,
    title: r.TITLE,
    video_path: r.VIDEO_PATH,
    image_path: r.IMAGE_PATH,
    ad_timing: r.AD_TIMING ?? 0,
    ad_duration: r.AD_DURATION ?? 0,
    match: r.MATCH_SCORE ?? undefined,
    rating: r.RATING ?? undefined,
    seasons: r.SEASONS ?? undefined,
    description: r.DESCRIPTION ?? undefined,
    year: r.YEAR ?? undefined,
  }));
}

async function pull() {
  const conn = await connect();
  try {
    const rows = await execute(conn, `SELECT id, title, video_path, image_path, ad_timing, ad_duration, match_score, rating, seasons, description, year FROM ${TABLE_NAME} ORDER BY id`);
    const movies = rowsToMovies(rows);
    fs.writeFileSync(MOVIES_JSON_PATH, JSON.stringify(movies, null, 2), "utf8");
    console.log(`Pulled ${movies.length} movies from Snowflake into ${MOVIES_JSON_PATH}.`);
  } finally {
    conn.destroy((err) => {
      if (err) console.error("Connection close error:", err);
    });
  }
}

/** Fetch movies from Snowflake and output JSON to stdout (for Vite /api/movies). */
async function fetch() {
  const conn = await connect();
  try {
    const rows = await execute(conn, `SELECT id, title, video_path, image_path, ad_timing, ad_duration, match_score, rating, seasons, description, year FROM ${TABLE_NAME} ORDER BY id`);
    const movies = rowsToMovies(rows);
    process.stdout.write(JSON.stringify(movies));
  } finally {
    conn.destroy((err) => {
      if (err) console.error("Connection close error:", err);
    });
  }
}

const cmd = process.argv[2];
if (cmd === "push") {
  push().catch((e) => {
    console.error(e);
    process.exit(1);
  });
} else if (cmd === "pull") {
  pull().catch((e) => {
    console.error(e);
    process.exit(1);
  });
} else if (cmd === "fetch") {
  fetch().catch((e) => {
    console.error(e);
    process.exit(1);
  });
} else {
  console.log("Usage: node scripts/snowflake-movies.cjs push | pull | fetch");
  process.exit(1);
}
