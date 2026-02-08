import argparse
import json
import os
from pathlib import Path
from typing import Any, Iterable

import snowflake.connector
from dotenv import load_dotenv


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_scene_rows(data: dict[str, Any], source_file: str) -> list[tuple[Any, ...]]:
    video_id = data.get("video_id")
    rows: list[tuple[Any, ...]] = []
    for scene in data.get("scenes", []):
        timestamp_range = scene.get("timestamp_range", [None, None])
        scene_start = timestamp_range[0] if len(timestamp_range) > 0 else None
        scene_end = timestamp_range[1] if len(timestamp_range) > 1 else None
        rows.append(
            (
                video_id,
                scene.get("scene_id"),
                scene_start,
                scene_end,
                json.dumps(scene.get("product_mentions", [])),
                source_file,
            )
        )
    return rows


def build_product_rows(data: dict[str, Any], source_file: str) -> list[tuple[Any, ...]]:
    video_id = data.get("video_id")
    rows: list[tuple[Any, ...]] = []
    for scene in data.get("scenes", []):
        timestamp_range = scene.get("timestamp_range", [None, None])
        scene_start = timestamp_range[0] if len(timestamp_range) > 0 else None
        scene_end = timestamp_range[1] if len(timestamp_range) > 1 else None
        scene_id = scene.get("scene_id")
        for mention in scene.get("product_mentions", []):
            evidence = mention.get("evidence", {}) or {}
            rows.append(
                (
                    video_id,
                    scene_id,
                    scene_start,
                    scene_end,
                    mention.get("product_name"),
                    mention.get("brand"),
                    mention.get("category"),
                    mention.get("confidence"),
                    evidence.get("visual"),
                    evidence.get("dialogue"),
                    source_file,
                )
            )
    return rows


def chunked(items: list[tuple[Any, ...]], size: int) -> Iterable[list[tuple[Any, ...]]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    raise RuntimeError(f"Missing required env var: {name}")


def get_connection() -> snowflake.connector.SnowflakeConnection:
    return snowflake.connector.connect(
        account=require_env("SNOWFLAKE_ACCOUNT"),
        user=require_env("SNOWFLAKE_USER"),
        password=require_env("SNOWFLAKE_PASSWORD"),
        role=os.getenv("SNOWFLAKE_ROLE"),
        warehouse=require_env("SNOWFLAKE_WAREHOUSE"),
        database=require_env("SNOWFLAKE_DATABASE"),
        schema=require_env("SNOWFLAKE_SCHEMA"),
    )


def create_schema_and_tables(cursor: snowflake.connector.cursor.SnowflakeCursor) -> None:
    warehouse = require_env("SNOWFLAKE_WAREHOUSE")
    database = require_env("SNOWFLAKE_DATABASE")
    schema = require_env("SNOWFLAKE_SCHEMA")
    cursor.execute("USE WAREHOUSE IDENTIFIER(%(warehouse)s)", {"warehouse": warehouse})
    cursor.execute("USE DATABASE IDENTIFIER(%(database)s)", {"database": database})
    cursor.execute("CREATE SCHEMA IF NOT EXISTS IDENTIFIER(%(schema)s)", {"schema": schema})
    cursor.execute("USE SCHEMA IDENTIFIER(%(schema)s)", {"schema": schema})
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS VIDEO_SCENES (
            VIDEO_ID STRING,
            SCENE_ID STRING,
            SCENE_START FLOAT,
            SCENE_END FLOAT,
            PRODUCT_MENTIONS VARIANT,
            SOURCE_FILE STRING,
            INGESTED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS PRODUCT_MENTIONS (
            VIDEO_ID STRING,
            SCENE_ID STRING,
            SCENE_START FLOAT,
            SCENE_END FLOAT,
            PRODUCT_NAME STRING,
            BRAND STRING,
            CATEGORY STRING,
            CONFIDENCE FLOAT,
            EVIDENCE_VISUAL STRING,
            EVIDENCE_DIALOGUE STRING,
            SOURCE_FILE STRING,
            INGESTED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
        )
        """
    )


def insert_rows(
    cursor: snowflake.connector.cursor.SnowflakeCursor,
    sql: str,
    rows: list[tuple[Any, ...]],
    batch_size: int,
) -> int:
    inserted = 0
    for batch in chunked(rows, batch_size):
        cursor.executemany(sql, batch)
        inserted += len(batch)
    return inserted


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Load structured product JSON into Snowflake.")
    parser.add_argument(
        "--inputs",
        nargs="+",
        required=True,
        help="JSON files to load.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Number of rows per batch insert.",
    )
    args = parser.parse_args()

    input_paths = [Path(path).expanduser().resolve() for path in args.inputs]
    for path in input_paths:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

    scene_rows: list[tuple[Any, ...]] = []
    product_rows: list[tuple[Any, ...]] = []
    for path in input_paths:
        data = load_json(path)
        scene_rows.extend(build_scene_rows(data, path.name))
        product_rows.extend(build_product_rows(data, path.name))

    with get_connection() as connection:
        with connection.cursor() as cursor:
            create_schema_and_tables(cursor)
            scene_inserted = insert_rows(
                cursor,
                """
                INSERT INTO VIDEO_SCENES (
                    VIDEO_ID,
                    SCENE_ID,
                    SCENE_START,
                    SCENE_END,
                    PRODUCT_MENTIONS,
                    SOURCE_FILE
                )
                SELECT
                    column1,
                    column2,
                    column3,
                    column4,
                    PARSE_JSON(column5),
                    column6
                FROM VALUES (%s, %s, %s, %s, %s, %s)
                """,
                scene_rows,
                args.batch_size,
            )
            product_inserted = insert_rows(
                cursor,
                """
                INSERT INTO PRODUCT_MENTIONS (
                    VIDEO_ID,
                    SCENE_ID,
                    SCENE_START,
                    SCENE_END,
                    PRODUCT_NAME,
                    BRAND,
                    CATEGORY,
                    CONFIDENCE,
                    EVIDENCE_VISUAL,
                    EVIDENCE_DIALOGUE,
                    SOURCE_FILE
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                product_rows,
                args.batch_size,
            )

    print(f"Inserted {scene_inserted} scene rows and {product_inserted} product rows.")


if __name__ == "__main__":
    main()
