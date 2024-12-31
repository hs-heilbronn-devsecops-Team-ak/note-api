# -*- coding: utf-8 -*-
from uuid import uuid4
from typing import List, Optional
from os import getenv
from typing_extensions import Annotated

from fastapi import Depends, FastAPI
from starlette.responses import RedirectResponse
from .backends import Backend, RedisBackend, MemoryBackend, GCSBackend
from .model import Note, CreateNoteRequest
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.cloud_trace import CloudTraceExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
from opentelemetry.context import attach
from opentelemetry.context import Context


# Add OpenTelemetry setup
trace.set_tracer_provider(TracerProvider())

# Create a Cloud Trace Exporter
cloud_trace_exporter = CloudTraceExporter()

# Add the exporter to the tracer provider
span_processor = BatchExportSpanProcessor(cloud_trace_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Initialize FastAPI app
app = FastAPI()

# Instrument FastAPI app to automatically trace all endpoints
FastAPIInstrumentor.instrument_app(app)

# Existing code with no changes
def get_backend() -> Backend:
    global my_backend  # pylint: disable=global-statement
    if my_backend is None:
        backend_type = getenv('BACKEND', 'memory')
        print(backend_type)
        if backend_type == 'redis':
            my_backend = RedisBackend()
        elif backend_type == 'gcs':
            my_backend = GCSBackend()
        else:
            my_backend = MemoryBackend()
    return my_backend

@app.get('/')
def redirect_to_notes() -> None:
    return RedirectResponse(url='/Notes')

@app.get('/notes')
def get_notes(backend: Annotated[Backend, Depends(get_backend)]) -> List[Note]:
    keys = backend.keys()

    Notes = []
    for key in keys:
        Notes.append(backend.get(key))
    return Notes

@app.get('/notes/{note_id}')
def get_note(note_id: str, backend: Annotated[Backend, Depends(get_backend)]) -> Note:
    return backend.get(note_id)

@app.put('/notes/{note_id}')
def update_note(note_id: str, request: CreateNoteRequest, backend: Annotated[Backend, Depends(get_backend)]) -> None:
    backend.set(note_id, request)

@app.post('/notes')
def create_note(request: CreateNoteRequest, backend: Annotated[Backend, Depends(get_backend)]) -> str:
    note_id = str(uuid4())
    backend.set(note_id, request)
    return note_id

@app.get('/notes')
def get_notes(backend: Annotated[Backend, Depends(get_backend)]) -> List[Note]:
    # Start custom span
    with trace.get_tracer(__name__).start_as_current_span("get_notes-span"):
        keys = backend.keys()
        Notes = []
        for key in keys:
            Notes.append(backend.get(key))
        return Notes
