Place Tree-sitter WASM files here to enable offline/local parsing.

Required files:

- tree-sitter.wasm (runtime from web-tree-sitter package)
- tree-sitter-javascript.wasm
- tree-sitter-typescript.wasm
- tree-sitter-python.wasm
- tree-sitter-java.wasm
- tree-sitter-go.wasm
- tree-sitter-rust.wasm

Notes:

- For dev: you can copy `tree-sitter.wasm` from `node_modules/web-tree-sitter/tree-sitter.wasm`.
- Language grammars can be built from their respective repositories or obtained as prebuilt `.wasm` artifacts.
- If a language wasm is missing, the parser will skip it and try to fallback to JavaScript.
