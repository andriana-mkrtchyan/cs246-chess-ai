from pathlib import Path

def make_gallery(svg_dir="fen_svgs", outfile="fen_gallery.html"):
    svg_dir = Path(svg_dir)
    svgs = sorted(svg_dir.glob("*.svg"))

    if not svgs:
        print(f"No SVG files found in {svg_dir}")
        return

    with open(outfile, "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Endgame Positions Gallery</title>
<style>
  body {
    font-family: Arial, sans-serif;
    padding: 20px;
  }
  h1 {
    text-align: center;
  }
  .grid {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    justify-content: center;
  }
  .card {
    border: 1px solid #ccc;
    padding: 8px;
    text-align: center;
  }
  .card img {
    width: 200px;      /* change if you want bigger/smaller boards */
    height: 200px;
    display: block;
  }
  .caption {
    margin-top: 4px;
    font-size: 12px;
    color: #555;
  }
</style>
</head>
<body>
<h1>Endgame Positions</h1>
<div class="grid">
""")

        for idx, svg_path in enumerate(svgs, start=1):
            rel_path = f"{svg_dir.name}/{svg_path.name}"
            f.write(f'''  <div class="card">
    <img src="{rel_path}" alt="Position {idx}">
    <div class="caption">Position {idx}</div>
  </div>
''')

        f.write("""</div>
</body>
</html>
""")

    print(f"Gallery written to: {outfile}")


if __name__ == "__main__":
    # adjust "fen_svgs" if your folder name is different
    make_gallery("fen_svgs", "fen_gallery.html")
