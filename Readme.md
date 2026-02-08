# Seamless
*Have a seamless experience with scene-aware Ads in streaming services!* Submission to Devfest 2026 at Columbia University

## Project
Seamless is an in-movie ad recommendation platform that turns streaming scenes into shoppable moments. It analyzes scenes, matches products to the right moment, and delivers non-disruptive overlays that feel native to the story.

## Flow
1. **Understand the scene and user**  
   Preprocess content to build a scene index, align transcripts with product moments, and personalize recommendations using viewer attributes.
2. **Invoke the shopping stack**  
   During playback, our MCP orchestration queries real-world inventory and selects the best matching products for the moment.
3. **Overlay and checkout**  
   Branded overlays appear directly on in-scene products, while the product surfaces in a sidebar for instant checkout or save-for-later.

## What We Built
- Scene understanding and indexing pipeline
- Product matching with real inventory lookups
- AI-powered product overlays that preserve narrative flow
- A Netflix-style frontend demo to visualize the experience

## Figma Link
[Figma Link](https://www.figma.com/design/Kp0Qqttd2zFr8WxsHhYQ3m/Netflix-replica?node-id=17-16&t=CbwDDoV2HzISE3FM-0)

## Snowflake Ingestion
Load the structured product JSON into Snowflake tables for scenes and product mentions.

### Setup
1. Install Python deps:
   `pip install -r requirements.txt`
2. Create a `.env` from `.env.example` and fill in your Snowflake credentials.

### Run
```
python scripts/load_structured_products_to_snowflake.py \
  --inputs outputs/BBS3E2_structured_products.json outputs/STS3E4_structured_products.json
```

### Output Tables
- `VIDEO_SCENES`: one row per scene with `PRODUCT_MENTIONS` as VARIANT.
- `PRODUCT_MENTIONS`: one row per product mention per scene.
