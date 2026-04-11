-- Agregar columna orador_id a tabla clases
ALTER TABLE clases 
ADD COLUMN orador_id INTEGER REFERENCES oradores(id) ON DELETE SET NULL;

CREATE INDEX idx_clases_orador_id ON clases(orador_id);
