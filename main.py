from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

app = FastAPI(title="Upload TXT API")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def next_available_path(filename: str) -> Path:
	original = Path(filename)
	stem = original.stem
	suffix = original.suffix.lower()

	candidate = UPLOAD_DIR / f"{stem}{suffix}"
	counter = 2

	while candidate.exists():
		candidate = UPLOAD_DIR / f"{stem}-{counter}{suffix}"
		counter += 1

	return candidate


def list_uploaded_files() -> list[str]:
	files = [path.name for path in UPLOAD_DIR.iterdir() if path.is_file() and path.suffix.lower() == ".txt"]
	return sorted(files)


@app.get("/", response_class=HTMLResponse)
async def home() -> str:
	return """<!doctype html>
<html lang="es">
	<head>
		<meta charset="utf-8" />
		<meta name="viewport" content="width=device-width,initial-scale=1" />
		<title>Subir TXT</title>
		<style>
			body { font-family: sans-serif; max-width: 560px; margin: 40px auto; padding: 0 16px; }
			form { display: grid; gap: 12px; }
			button { width: fit-content; padding: 8px 14px; }
			#out { margin-top: 16px; padding: 10px; border: 1px solid #ddd; border-radius: 8px; white-space: pre-wrap; }
			#files { margin-top: 24px; }
			#files ul { padding-left: 20px; }
		</style>
	</head>
	<body>
		<h1>Subir archivo .txt</h1>
		<form id="uploadForm">
			<input id="fileInput" type="file" name="file" accept=".txt,text/plain" required />
			<button type="submit">Subir</button>
		</form>
		<div id="out">Esperando archivo...</div>

		<section id="files">
			<h2>Archivos disponibles</h2>
			<button id="refreshFiles" type="button">Actualizar listado</button>
			<ul id="filesList"></ul>
		</section>

		<script>
			const form = document.getElementById("uploadForm");
			const out = document.getElementById("out");
			const filesList = document.getElementById("filesList");
			const refreshFilesButton = document.getElementById("refreshFiles");

			async function loadFiles() {
				filesList.innerHTML = "<li>Cargando...</li>";
				try {
					const response = await fetch("/files");
					const payload = await response.json();

					if (!response.ok) {
						filesList.innerHTML = "<li>Error al cargar archivos</li>";
						return;
					}

					filesList.innerHTML = "";
					if (!payload.files.length) {
						filesList.innerHTML = "<li>No hay archivos todavía.</li>";
						return;
					}

					for (const filename of payload.files) {
						const item = document.createElement("li");
						const link = document.createElement("a");
						link.href = "/download/" + encodeURIComponent(filename);
						link.textContent = filename;
						item.appendChild(link);
						filesList.appendChild(item);
					}
				} catch (error) {
					filesList.innerHTML = "<li>Error de red: " + error.message + "</li>";
				}
			}

			form.addEventListener("submit", async (event) => {
				event.preventDefault();

				const input = document.getElementById("fileInput");
				if (!input.files.length) {
					out.textContent = "Selecciona un archivo primero.";
					return;
				}

				const data = new FormData();
				data.append("file", input.files[0]);

				try {
					const response = await fetch("/upload", { method: "POST", body: data });
					const payload = await response.json();

					if (!response.ok) {
						out.textContent = "Error: " + (payload.detail || "No se pudo subir");
						return;
					}

					out.textContent = "OK\\nGuardado como: " + payload.saved_as + "\\nRuta: " + payload.path;
					await loadFiles();
				} catch (error) {
					out.textContent = "Error de red: " + error.message;
				}
			});

			refreshFilesButton.addEventListener("click", loadFiles);
			loadFiles();
		</script>
	</body>
</html>
"""


@app.get("/files")
async def get_files():
	return {"files": list_uploaded_files()}


@app.get("/download/{filename}")
async def download_file(filename: str):
	if Path(filename).name != filename:
		raise HTTPException(status_code=400, detail="Nombre de archivo inválido")

	if Path(filename).suffix.lower() != ".txt":
		raise HTTPException(status_code=400, detail="Solo se permiten archivos .txt")

	file_path = UPLOAD_DIR / filename
	if not file_path.exists() or not file_path.is_file():
		raise HTTPException(status_code=404, detail="Archivo no encontrado")

	return FileResponse(path=file_path, media_type="text/plain; charset=utf-8", filename=filename)


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
	if not file.filename:
		raise HTTPException(status_code=400, detail="Debes enviar un archivo")

	if Path(file.filename).suffix.lower() != ".txt":
		raise HTTPException(status_code=400, detail="Solo se permiten archivos .txt")

	content = await file.read()

	try:
		content.decode("utf-8")
	except UnicodeDecodeError as exc:
		raise HTTPException(status_code=400, detail="El archivo debe estar en UTF-8") from exc

	destination = next_available_path(file.filename)
	destination.write_bytes(content)

	return {
		"message": "Archivo guardado correctamente",
		"saved_as": destination.name,
		"path": str(destination),
	}