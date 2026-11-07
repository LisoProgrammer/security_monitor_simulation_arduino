const int LED_VERDE = 4;
const int LED_AMARILLO = 5;
const int LED_ROJO = 6;

const int BTN_INTENTAR = 10;
const int BTN_RESET = 11;

const int BUZZER = 12;

int intentos = 0;

const int LIMITE_VERDE = 3;
const int LIMITE_AMARILLO = 6;
const int LIMITE_ROJO = 7;

// Variables para antirrebote
int estadoIntentar = HIGH;
int lecturaIntentar = HIGH;
unsigned long tiempoIntentar = 0;

int estadoReset = HIGH;
int lecturaReset = HIGH;
unsigned long tiempoReset = 0;

const unsigned long DEBOUNCE = 50;

// Detectar una pulsación
bool detectarPulsacion(
  int pin,
  int &estadoEstable,
  int &ultimaLectura,
  unsigned long &ultimoCambio
) {
  int lectura = digitalRead(pin);

  if (lectura != ultimaLectura) {
    ultimoCambio = millis();
    ultimaLectura = lectura;
  }

  if (millis() - ultimoCambio >= DEBOUNCE) {
    if (lectura != estadoEstable) {
      estadoEstable = lectura;

      if (estadoEstable == LOW) {
        return true;
      }
    }
  }

  return false;
}

// Actualizar LED y buzzer

void actualizarSistema() {
  // Apagar todas las salidas
  digitalWrite(LED_VERDE, LOW);
  digitalWrite(LED_AMARILLO, LOW);
  digitalWrite(LED_ROJO, LOW);

  noTone(BUZZER);

  if (intentos >= 1 && intentos <= 3) {
    digitalWrite(LED_VERDE, HIGH);
    Serial.println("NIVEL VERDE: ACTIVIDAD NORMAL");

  } else if (intentos >= 4 && intentos <= 6) {
    digitalWrite(LED_AMARILLO, HIGH);
    Serial.println("NIVEL AMARILLO: ADVERTENCIA");

  } else if (intentos >= 7) {
    digitalWrite(LED_ROJO, HIGH);
    tone(BUZZER, 1000);

    Serial.println("NIVEL ROJO: ALERTA DE SEGURIDAD");
    Serial.println("ALARMA SONORA ACTIVADA");

  } else {
    Serial.println("SISTEMA EN ESPERA");
  }
}


void setup() {
  pinMode(LED_VERDE, OUTPUT);
  pinMode(LED_AMARILLO, OUTPUT);
  pinMode(LED_ROJO, OUTPUT);

  pinMode(BTN_INTENTAR, INPUT_PULLUP);
  pinMode(BTN_RESET, INPUT_PULLUP);

  pinMode(BUZZER, OUTPUT);

  Serial.begin(9600);

  Serial.println("================================");
  Serial.println(" SISTEMA DE SEGURIDAD INICIADO");
  Serial.println("================================");

  actualizarSistema();
}

void loop() {

  bool resetPresionado = detectarPulsacion(
    BTN_RESET,
    estadoReset,
    lecturaReset,
    tiempoReset
  );

  bool intentarPresionado = detectarPulsacion(
    BTN_INTENTAR,
    estadoIntentar,
    lecturaIntentar,
    tiempoIntentar
  );

  // Reiniciar sistema
  if (resetPresionado) {
    intentos = 0;

    Serial.println();
    Serial.println("!!! SISTEMA REINICIADO !!!");
    Serial.println("Contador de intentos: 0");

    actualizarSistema();
  }

  // Registrar intento
  else if (intentarPresionado) {
    intentos++;

    Serial.println();
    Serial.print("INTENTO REGISTRADO: ");
    Serial.println(intentos);

    actualizarSistema();
  }
}