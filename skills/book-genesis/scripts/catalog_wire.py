"""Lossless review catalogs without escaping every prose line break as JSON."""
import json


def render_catalog(catalog):
    rows = []
    for source in catalog["sources"]:
        header = {k: source[k] for k in ("source", "sha256")}
        header["passage_count"] = len(source["passages"])
        rows.append("S " + json.dumps(header, ensure_ascii=False, separators=(",", ":")) + "\n")
        for passage in source["passages"]:
            text = passage["text"]
            rows.append(f"P {passage['id']} {len(text)}\n{text}\n")
    return "".join(rows)


def parse_catalog(wire):
    """Reconstruct the exact catalog; prose cannot masquerade as wire headers."""
    offset = 0
    sources = []
    while offset < len(wire):
        end = wire.index("\n", offset)
        line = wire[offset:end]
        if not line.startswith("S "):
            raise ValueError("Missing source header")
        header = json.loads(line[2:])
        offset = end + 1
        passages = []
        for _ in range(header["passage_count"]):
            end = wire.index("\n", offset)
            parts = wire[offset:end].split()
            if len(parts) != 3 or parts[0] != "P" or not parts[2].isdigit():
                raise ValueError("Invalid passage header")
            start = end + 1
            end = start + int(parts[2])
            if end >= len(wire) or wire[end] != "\n":
                raise ValueError("Truncated passage")
            passages.append({"id": parts[1], "text": wire[start:end]})
            offset = end + 1
        sources.append({"source": header["source"], "sha256": header["sha256"], "passages": passages})
    return {"sources": sources}
