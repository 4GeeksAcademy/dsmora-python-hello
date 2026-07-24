import csv
from pathlib import Path

CSV_FILE = Path("tareas.csv")


def ensure_csv_exists() -> None:
	if not CSV_FILE.exists():
		with CSV_FILE.open("w", newline="", encoding="utf-8") as file:
			writer = csv.writer(file)
			writer.writerow(["id", "tarea"])


def get_next_id() -> int:
	ensure_csv_exists()
	last_id = 0

	with CSV_FILE.open("r", newline="", encoding="utf-8") as file:
		reader = csv.DictReader(file)
		for row in reader:
			try:
				current_id = int(row.get("id", 0))
				if current_id > last_id:
					last_id = current_id
			except ValueError:
				continue

	return last_id + 1


def create_todo() -> None:
	task_text = input("Escribe la tarea: ").strip()

	if not task_text:
		print("La tarea no puede estar vacia.")
		return

	task_id = get_next_id()

	with CSV_FILE.open("a", newline="", encoding="utf-8") as file:
		writer = csv.writer(file)
		writer.writerow([task_id, task_text])

	print(f"Tarea creada con ID {task_id}.")


def view_todos() -> None:
	ensure_csv_exists()

	with CSV_FILE.open("r", newline="", encoding="utf-8") as file:
		reader = csv.DictReader(file)
		tasks = list(reader)

	if not tasks:
		print("No hay tareas guardadas.")
		return

	print("\nLista de tareas:")
	for task in tasks:
		print(f"{task['id']}. {task['tarea']}")

def delete_todo(id: int) -> None:
	ensure_csv_exists()

	tasks = []
	with CSV_FILE.open("r", newline="", encoding="utf-8") as file:
		reader = csv.DictReader(file)
		tasks = list(reader)
	
	if not any(int(task["id"]) == id for task in tasks):
		print(f"No se encontro tarea con ID {id}.")
		return

	tasks = [task for task in tasks if int(task["id"]) != id]

	with CSV_FILE.open("w", newline="", encoding="utf-8") as file:
		writer = csv.DictWriter(file, fieldnames=["id", "tarea"])
		writer.writeheader()
		writer.writerows(tasks)

	print(f"Tarea con ID {id} eliminada.")


def show_menu() -> None:
	print("\n--- MENU TODO ---")
	print("1. Ver todos")
	print("2. Crear todo")
	print("3. Eliminar todo")
	print("4. Salir")


def main() -> None:
	ensure_csv_exists()

	while True:
		show_menu()
		option = input("Elige una opcion: ").strip()

		if option == "1":
			view_todos()
		elif option == "2":
			create_todo()
		elif option == "3":
			try:
				task_id = int(input("Ingresa el ID de la tarea a eliminar: ").strip())
				delete_todo(task_id)
			except ValueError:
				print("ID invalido. Por favor ingresa un numero entero.")
		elif option == "4":
			print("Hasta luego.")
			break
		else:
			print("Opcion invalida. Intenta de nuevo.")


if __name__ == "__main__":
	main()