"""Modal web endpoint for sharing drug design datasets.

Provides:
  - /list   — browsable file index with download links
  - /download?path=DualDiff/data/processed/dock/index_dict.pkl — single file download
  - /download-repo?repo=DualDiff — download entire repo as tar.gz

Deploy:  modal deploy share_data.py
"""
import modal

app = modal.App("drug-design-share")

volume = modal.Volume.from_name("drug-design-data")

image = modal.Image.debian_slim(python_version="3.11").pip_install("fastapi[standard]")

MOUNT_PATH = "/data"
REPOS_DIR = f"{MOUNT_PATH}/repos"


@app.function(
    image=image,
    volumes={MOUNT_PATH: volume},
)
@modal.fastapi_endpoint(method="GET", label="drug-design-share-list")
def list_files():
    import os
    from fastapi.responses import HTMLResponse

    files = []
    for repo in sorted(os.listdir(REPOS_DIR)):
        repo_path = os.path.join(REPOS_DIR, repo)
        if not os.path.isdir(repo_path) or repo.startswith("."):
            continue
        for root, dirs, fnames in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d != ".git"]
            for fname in fnames:
                fpath = os.path.join(root, fname)
                rel = os.path.relpath(fpath, REPOS_DIR)
                size = os.path.getsize(fpath)
                if size > 0:
                    files.append({"path": rel, "size": size, "h": _human_size(size)})

    total_size = sum(f["size"] for f in files)

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Multi-Target Drug Design Data</title>
<style>
body {{ font-family: -apple-system, sans-serif; max-width: 960px; margin: 40px auto; padding: 0 20px; }}
h1 {{ color: #333; }}
.summary {{ background: #e8f5e9; padding: 12px 16px; border-radius: 6px; margin-bottom: 20px; }}
.quick {{ background: #e3f2fd; padding: 12px 16px; border-radius: 6px; margin-bottom: 20px; }}
.quick code {{ background: #fff; padding: 2px 6px; border-radius: 3px; }}
.repo {{ margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
.repo h2 {{ margin: 0 0 10px; color: #0066cc; }}
.repo .dl-btn {{ display: inline-block; margin-left: 10px; padding: 2px 10px; background: #0066cc; color: #fff; border-radius: 4px; font-size: 0.85em; text-decoration: none; }}
.repo .dl-btn:hover {{ background: #004999; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ text-align: left; padding: 6px 12px; border-bottom: 1px solid #eee; }}
th {{ background: #e9ecef; }}
a {{ color: #0066cc; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
.size {{ color: #666; font-size: 0.9em; }}
</style></head><body>
<h1>Multi-Target Drug Design Datasets</h1>
<div class="summary">
<strong>Total:</strong> {len(files)} files, {_human_size(total_size)}<br>
<strong>目标论文:</strong> DualDiff (NeurIPS 2024) + MM-MT (ICML 2026)<br>
<strong>依赖:</strong> TargetDiff (ICLR 2023) — DualDiff 的预训练基础模型，非目标论文
</div>
<div class="quick">
<strong>Quick download (whole repo as tar.gz):</strong><br>
"""

    repos = sorted(set(f["path"].split("/")[0] for f in files))
    for repo in repos:
        html += f'<code>curl -LO "BASE_URL/download-repo?repo={repo}"</code><br>'

    html += "</div>"

    current_repo = None
    for f in sorted(files, key=lambda x: x["path"]):
        repo = f["path"].split("/")[0]
        if repo != current_repo:
            if current_repo:
                html += "</table></div>"
            current_repo = repo
            html += (
                f'<div class="repo"><h2>{repo}'
                f'<a class="dl-btn" href="/download-repo?repo={repo}">Download .tar.gz</a>'
                f'</h2><table><tr><th>File</th><th>Size</th></tr>'
            )

        name = "/".join(f["path"].split("/")[1:])
        display = ("..." + name[-77:]) if len(name) > 80 else name
        html += f'<tr><td><a href="/download?path={f["path"]}">{display}</a></td><td class="size">{f["h"]}</td></tr>'

    if current_repo:
        html += "</table></div>"

    html += """
<div style="margin-top:30px;color:#999;font-size:0.85em">
Replace <code>BASE_URL</code> with this page's domain in the curl commands above.
</div>
</body></html>"""

    return HTMLResponse(content=html)


@app.function(
    image=image,
    volumes={MOUNT_PATH: volume},
    timeout=600,
)
@modal.fastapi_endpoint(method="GET", label="drug-design-share-download")
def download(path: str = ""):
    import os
    from fastapi.responses import FileResponse, JSONResponse

    if not path or ".." in path:
        return JSONResponse({"error": "Invalid path"}, status_code=400)

    full_path = os.path.join(REPOS_DIR, path)
    if not os.path.isfile(full_path):
        return JSONResponse({"error": f"File not found: {path}"}, status_code=404)

    filename = os.path.basename(path)
    return FileResponse(full_path, filename=filename, media_type="application/octet-stream")


@app.function(
    image=image,
    volumes={MOUNT_PATH: volume},
    timeout=1800,
)
@modal.fastapi_endpoint(method="GET", label="drug-design-share-download-repo")
def download_repo(repo: str = ""):
    import os, tarfile, tempfile
    from fastapi.responses import FileResponse, JSONResponse

    if not repo or ".." in repo or "/" in repo:
        return JSONResponse({"error": "Invalid repo name"}, status_code=400)

    repo_path = os.path.join(REPOS_DIR, repo)
    if not os.path.isdir(repo_path):
        return JSONResponse({"error": f"Repo not found: {repo}"}, status_code=404)

    tmp = tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False)
    tmp.close()

    with tarfile.open(tmp.name, "w:gz") as tar:
        for root, dirs, fnames in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d != ".git"]
            for fname in fnames:
                fpath = os.path.join(root, fname)
                arcname = os.path.relpath(fpath, REPOS_DIR)
                tar.add(fpath, arcname=arcname)

    return FileResponse(tmp.name, filename=f"{repo}.tar.gz", media_type="application/gzip")


def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
