/// Event Envelope for telemetry events in the frontend application.

const maxEvents = 10;
const timeToLive = 60; // Time to live for events in seconds

const localEvents = [{
  "eventId": "string",
  "event": "string",
  "schemaVersion": "string",
  "timestamp": "string",
  "userId": "string",
  "sessionId": "string",
  "context": {},
  "properties": {
    "userSearch": "", 
    "documentPath": "../frontend/telemetry.ts"
  },
  "metadata": { source: 'frontend-web', environment: "dev", appVersion: "1.0.0" }
}, {
  "eventId": "string",
  "event": "string",
  "schemaVersion": "string",
  "timestamp": "string",
  "userId": "string",
  "sessionId": "string",
  "context": {},
  "properties": {},
  "metadata": { source: 'frontend-web', environment: "dev", appVersion: "1.0.0" }
}, {
  "eventId": "string",
  "event": "string",
  "schemaVersion": "string",
  "timestamp": "string",
  "userId": "string",
  "sessionId": "string",
  "context": {},
  "properties": {
    "email": "test6@test.com",
    "pageTarget": "",
    "slotView": "",
    "action": "clickToBuy"
  },
  "metadata": { source: 'frontend-web', environment: "dev", appVersion: "1.0.0" }
}];

const maxLimitReintent = 3;
let reintentCount = 0;

if(localEvents.length > 0) {
    try {
        fetch('/api/telemetry', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(localEvents)
    });
    }
    catch (error) {
        // Retry logic can be implemented here if needed, up to maxLimitReintent attempts.
        if (reintentCount < maxLimitReintent) {
            reintentCount++;
            let entrophy = Math.random();
            let retryDelay = reintentCount === 1 
            ? 1000 * reintentCount + entrophy * 1000
            : 1000 * reintentCount**2 + entrophy * 1000; // Retry after 1 second
            // Retry sending the telemetry events
            setTimeout(() => {
                fetch('/api/telemetry', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(localEvents)
                });
            }, retryDelay); // Retry after 1 second
        }
        console.error('Failed to send telemetry events:', error);
    }
    
}

navigator.sendBeacon('/api/telemetry', JSON.stringify(localEvents));

// guardRails to ensure we do not exceed the maximum number of events stored locally
// 5 puntos de verificacion 
// 1 verificar consentimiento 
// 2 limpieza - sanitizar los datos
// 3 whitelist - propiedades permitidas
// 4 sampling - seleccionar una muestra representativa de eventos
// 5 select environment - asegurarse de que los eventos se envían al entorno correcto (dev, staging, prod)


// 3 puntos 

// donde inicia la telemtria _app.tsx 
// la logica debe ir en lib/telemetry.ts
// se puede colocar la lógica para inicializar la recolección de eventos de telemetría aquí
// que eventos queremos medir/recolectar 
// vista de libro, vista de home, filtros, reserva, login, registro
// diferenciar entre eventos del usuario y errores (Deteccion de errorres en rreact hay que usar el ErrorBoundary)
// usar batch para enviar múltiples eventos de telemetría juntos, en lugar de enviarlos individualmente
// asegurarse de limpiar los eventos locales después de enviarlos correctamente para evitar duplicados
