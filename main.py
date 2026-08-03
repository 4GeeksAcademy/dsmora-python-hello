### TinyDB - Diccionario de datos en memoria y persistente en JSON
### PyDantic - Validacion de datos
### CRUD - Create, Read, Update, Delete
### FastAPI 

from tinydb import TinyDB
from pydantic import BaseModel, Field, ValidationError
from enum import Enum


students = []
db = TinyDB("students_db.json")
students_table = db.table("students")


class CityEnum(str, Enum):
	MADRID = "Madrid"
	ALICANTE = "Alicante"
	BARCELONA = "Barcelona"


class Student(BaseModel):
	name: str = Field(min_length=1)
	age: int = Field(gt=0)
	city: CityEnum


def load_students():
	# Mantiene la lista en memoria sincronizada con TinyDB para el ejemplo actual.
	students.clear()
	students.extend(students_table.all())


def add_student(name, age, city):
	student_model = Student(name=name, age=age, city=city)
	student = student_model.model_dump(mode="json")
	students_table.insert(student)
	students.append(student)


def search_students_by_name(name_query):
	results = []
	for item in students_table.all():
		current_name = item.get("name")
		if current_name and name_query.lower() in current_name.lower():
			results.append(item)

	return results


def students_cli():
	while True:
		print("\nOpciones: 1. listar estudiante | 2. añadir | 3. buscar | 4. salir")
		option = input("Selecciona una opción: ").strip().lower()

		if option == "1" or option == "listar estudiante":
			load_students()
			if not students:
				print("No hay estudiantes registrados.")
				continue

			print("Estudiantes:")
			for index, student in enumerate(students, start=1):
				print(
					f"{index}. Nombre: {student['name']} | Edad: {student['age']} | Ciudad: {student['city']}"
				)

		elif option == "2" or option == "añadir":
			name = input("Nombre del alumno: ").strip()
			age_input = input("Edad del alumno: ").strip()
			city = input("Ciudad del alumno: ").strip()

			try:
				age = int(age_input)
			except ValueError:
				print("La edad debe ser un número entero.")
				continue

			try:
				add_student(name, age, city)
				print(f"Alumno '{name}' añadido correctamente.")
			except ValidationError as error:
				print("Datos inválidos:")
				for issue in error.errors():
					field = issue["loc"][0]
					print(f"- {field}: {issue['msg']}")

		elif option == "3" or option == "buscar":
			name_query = input("Nombre a buscar: ").strip()
			if not name_query:
				print("Debes escribir un nombre para buscar.")
				continue

			results = search_students_by_name(name_query)
			if not results:
				print("No se encontraron estudiantes con ese nombre.")
				continue

			print("Resultados:")
			for index, student in enumerate(results, start=1):
				print(
					f"{index}. Nombre: {student['name']} | Edad: {student['age']} | Ciudad: {student['city']}"
				)

		elif option == "4" or option == "salir":
			print("Saliendo del programa...")
			break

		else:
			print("Opción no válida. Usa: listar estudiante, añadir, buscar o salir.")


if __name__ == "__main__":
	students_cli()



