from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

app = FastAPI(
	title="API de Contactos",
	docs_url="/docs",
	openapi_url="/openapi.json",
)


class ContactBase(BaseModel):
	model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
	name: str = Field(min_length=1)
	tlf: str = Field(min_length=1)

	@field_validator("name", "tlf")
	@classmethod
	def validate_non_empty(cls, value: str) -> str:
		if not value.strip():
			raise ValueError("no puede estar vacío")
		return value.strip()


class ContactCreate(ContactBase):
	pass


class ContactPatch(BaseModel):
	model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
	name: str | None = Field(default=None, min_length=1)
	tlf: str | None = Field(default=None, min_length=1)

	@field_validator("name", "tlf")
	@classmethod
	def validate_optional_non_empty(cls, value: str | None) -> str | None:
		if value is not None and not value.strip():
			raise ValueError("no puede estar vacío")
		return value.strip() if value is not None else None

	@model_validator(mode="after")
	def validate_at_least_one_field(self) -> "ContactPatch":
		if self.name is None and self.tlf is None:
			raise ValueError("Debe enviar al menos un campo")
		return self


class ContactResponse(ContactBase):
	id: int


# Memoria local: lista de diccionarios
contacts = [
	{"id": 1, "name": "Juan", "tlf": "123456789"},
    {"id": 2, "name": "María", "tlf": "987654321"},
]


def find_contact_index(contact_id: int) -> int:
	for index, contact in enumerate(contacts):
		if contact["id"] == contact_id:
			return index
	return -1


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	errors = exc.errors()
	if any(error.get("loc", ())[-1] == "id" and error.get("type") == "extra_forbidden" for error in errors):
		detail = "id no permitido"
	elif any(error.get("type") == "missing" for error in errors):
		detail = "Debe incluir name y tlf"
	elif any(error.get("type") == "value_error" for error in errors):
		detail = errors[0]["msg"].replace("Value error, ", "")
	else:
		detail = "Datos inválidos"
	return JSONResponse(status_code=400, content={"detail": detail})


@app.get("/")
def health():
	return {"message": "API de contactos activa"}


@app.get("/contacts", response_model=list[ContactResponse])
def get_contacts(name: str | None = None, tlf: str | None = None, contact_id: int | None = None):
	results = contacts

	if contact_id is not None:
		results = [c for c in results if c["id"] == contact_id]
	if name is not None:
		results = [c for c in results if name.lower() in c["name"].lower()]
	if tlf is not None:
		results = [c for c in results if tlf in c["tlf"]]

	return [ContactResponse.model_validate(contact) for contact in results]


@app.get("/contacts/{contact_id}", response_model=ContactResponse)
def get_contact_by_id(contact_id: int):
	index = find_contact_index(contact_id)
	if index == -1:
		raise HTTPException(status_code=404, detail="Contacto no encontrado")
	return ContactResponse.model_validate(contacts[index])


@app.post("/contacts", response_model=ContactResponse, status_code=201)
async def create_contact(contact: ContactCreate):
	next_id = 1
	if contacts:
		next_id = max(existing_contact["id"] for existing_contact in contacts) + 1

	new_contact = {"id": next_id, "name": contact.name, "tlf": contact.tlf}
	contacts.append(new_contact)
	return ContactResponse.model_validate(new_contact)


@app.put("/contacts/{contact_id}", response_model=ContactResponse)
async def replace_contact(contact_id: int, contact: ContactCreate):
	index = find_contact_index(contact_id)
	if index == -1:
		raise HTTPException(status_code=404, detail="Contacto no encontrado")

	updated_contact = {"id": contact_id, "name": contact.name, "tlf": contact.tlf}
	contacts[index] = updated_contact
	return ContactResponse.model_validate(updated_contact)


@app.patch("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: int, contact: ContactPatch):
	index = find_contact_index(contact_id)
	if index == -1:
		raise HTTPException(status_code=404, detail="Contacto no encontrado")

	updated = contacts[index].copy()

	if contact.name is not None:
		updated["name"] = contact.name
	if contact.tlf is not None:
		updated["tlf"] = contact.tlf

	contacts[index] = updated
	return ContactResponse.model_validate(updated)


@app.delete("/contacts/{contact_id}")
def delete_contact(contact_id: int):
	index = find_contact_index(contact_id)
	if index == -1:
		raise HTTPException(status_code=404, detail="Contacto no encontrado")

	deleted = contacts.pop(index)
	return {"message": "Contacto eliminado", "contact": deleted}

