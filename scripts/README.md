Scripts Layout

- pipelines
  - langgraph
    - textbook_toc_pipeline_langgraph.py — Gemini recommends textbooks; Kimi fetches TOCs
    - integrated_textbook_pipeline_langgraph.py — end-to-end: recommend → fetch TOCs → reconstruct outline
    - reconstruct_outline_langgraph.py — reconstruct course outline from textbook TOCs
  - generation
    - full_pipeline.py — orchestrates outline stage → chapter generation stage
    - generate_chapters_from_integrated.py — chapter generation using run_full nodes
    - generate_chapters_from_integrated_standalone.py — chapter generation (self-contained nodes)
    - generate_outline_pipeline.py — 4-stage outline pipeline (Brainstorm → Structure → Detail → Review)
    - generate_outline.py — simplified outline generator
- tools
  - images
    - png_white_to_alpha.py, png_to_svg_potrace.py, svg_crop.py
  - content
    - cleanup_js_content.py, extract_code_examples.py
  - classification
    - archetype_classifier.py (rules+optional LLM hook), archetype_classifier_llm.py (LLM-only)
  - icons
    - generate_course_icon.py — generate small icons via Gemini
- experiments
  - chatgpt-quick.py, kimi-quick.py — quick demos (not production)

Notes

- Imports: scripts is now a Python package with subpackages; import paths use `scripts.<subpkg>...`.
- Repo root discovery: pipeline scripts now robustly locate the project root by walking up to the first directory containing `config.json`.
- Backwards compatibility: use the new paths shown above. If you had hard-coded CLI calls like `python scripts/<old>.py`, update to the new subpaths.

