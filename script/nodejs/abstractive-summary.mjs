// Paso 1: Importar la función 'pipeline' desde el paquete instalado
import { pipeline } from '@xenova/transformers';

// Paso 2: Pega el mismo objeto NLP_Toolkit_IA de la respuesta anterior.
// La única diferencia es cómo importamos 'pipeline' dentro de init().
const NLP_Toolkit_IA = {
    summarizer: null,
    nerTagger: null,

    async init(progress_callback = null) {
        console.log("Cargando modelo de resumen...");
        this.summarizer = await pipeline('summarization', 'Xenova/distilbart-cnn-6-6', { progress_callback });
        
        console.log("Cargando modelo de extracción de conceptos (NER)...");
        this.nerTagger = await pipeline('token-classification', 'Xenova/bert-base-multilingual-cased-ner-hrl', { progress_callback });
        
        console.log("¡Modelos de IA listos!");
    },

    preprocessText(text) {
        let cleanText = text;
        cleanText = cleanText.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '');
        cleanText = cleanText.replace(/\b([A-ZÁÉÍÓÚÜ]{2,})\b\s*\([^)]+\)/g, '$1');
        cleanText = cleanText.replace(/```[\s\S]*?```/g, '');
        cleanText = cleanText.replace(/!\[[^\]]*\]\([^\)]+\)/g, '');
        cleanText = cleanText.replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1');
        cleanText = cleanText.replace(/(\*\*|__|\*|_|~~|`)(.*?)\1/g, '$2');
        cleanText = cleanText.replace(/^#+\s*|^>\s*|^\s*[\*\-\+]\s*|^\s*\d+\.\s*/gm, '');
        cleanText = cleanText.replace(/--/g, ' ');
        cleanText = cleanText.replace(/\*/g, '');
        cleanText = cleanText.replace(/(\r\n|\n|\r)/gm, " ");
        cleanText = cleanText.replace(/\s+/g, ' ');
        return cleanText.trim();
    },

    async summarize(text, options = {}) {
        if (!this.summarizer) throw new Error("Llama a `init()` primero.");
        const config = { minLength: 30, maxLength: 150, intro: "En resumen, ", ...options };
        if (!text || text.trim().length < 100) return "El texto es demasiado corto.";
        const cleanText = this.preprocessText(text);
        const output = await this.summarizer(cleanText, {
            min_length: config.minLength,
            max_length: config.maxLength,
        });
        return config.intro + output[0].summary_text;
    },

    async extractKeyConcepts(text, minScore = 0.95) {
        if (!this.nerTagger) throw new Error("Llama a `init()` primero.");
        const cleanText = this.preprocessText(text);
        const entities = await this.nerTagger(cleanText, { aggregation_strategy: 'simple' });
        const concepts = new Set();
        entities
            .filter(entity => entity.score >= minScore)
            .forEach(entity => {
                const concept = entity.word.trim().replace(/^[#\s]+|[#\s]+$/g, '');
                if (concept.length > 2) concepts.add(concept);
            });
        return Array.from(concepts);
    }
};

// Paso 3: Crear una función principal asíncrona para ejecutar el análisis
async function main() {
    console.log("Iniciando el analizador de texto NLP...");

    // Texto de ejemplo sobre Guadalajara de Buga
    const textoDeEjemplo = `
       ¡Genial! Te hablo de **VPN (Virtual Private Network)** de forma clara 🚀

---

## 🔹 ¿Qué es una VPN?

Una **VPN (Red Privada Virtual)** es una tecnología que crea un **túnel seguro y cifrado** entre tu dispositivo (PC, móvil, servidor) e internet o una red privada.
En palabras simples: es como si enviaras tu información dentro de un “tubo secreto” que nadie más puede ver.

---

## 🔹 ¿Para qué sirve?

1. **Privacidad en internet**

   * Oculta tu dirección IP real.
   * Tu tráfico se ve como si viniera desde el servidor VPN.

2. **Seguridad en conexiones públicas**

   * Protege datos cuando usas Wi-Fi público (cafeterías, aeropuertos).

3. **Acceso remoto seguro**

   * Empleados de una empresa pueden conectarse a la red interna desde cualquier lugar.

4. **Acceso a contenido restringido**

   * Permite conectarte como si estuvieras en otro país.

---

## 🔹 Cómo funciona

1. Instalas un cliente VPN en tu dispositivo.
2. Te conectas a un **servidor VPN**.
3. El tráfico de tu dispositivo pasa por un **túnel cifrado** → viaja seguro hasta el servidor VPN.
4. Desde el servidor VPN, sale hacia internet.

Ejemplo:

* Sin VPN → tu tráfico va directo a internet (exponiendo tu IP real).
* Con VPN → tu tráfico va cifrado → servidor VPN → internet (se ve como si fuera el servidor quien navega).

---

## 🔹 Tipos de VPN

1. **VPN de acceso remoto**

   * Para que usuarios individuales se conecten a la red de la empresa.
   * Ejemplo: un empleado accediendo a la intranet de la compañía.

2. **VPN de sitio a sitio**

   * Conecta **dos redes completas** (ejemplo: oficinas en diferentes ciudades).

3. **VPN comerciales**

   * Servicios como NordVPN, ExpressVPN, Surfshark, que te dan privacidad y acceso global.

---

## 🔹 Protocolos más comunes

* **OpenVPN**: muy usado, seguro, flexible.
* **IPsec**: estándar para VPN en empresas.
* **WireGuard**: rápido, moderno y ligero.
* **SSL/TLS**: usado para conexiones seguras tipo VPN web.

---

## 🔹 Ventajas

✅ Cifrado de datos.
✅ Privacidad y anonimato.
✅ Acceso seguro a redes privadas.
✅ Protección en redes públicas.

## 🔹 Desventajas

⚠️ Puede reducir la velocidad (depende del servidor).
⚠️ No protege contra virus/malware (solo el tráfico).
⚠️ Algunas webs bloquean tráfico de VPN.

---

👉 ¿Quieres que te muestre un **ejemplo visual de cómo funciona una VPN con un diagrama**, o prefieres que lo explique con un **caso práctico en una empresa** (tipo: trabajadores remotos conectando a la red interna)?

    `;

    try {
        // Inicializa los modelos (solo se necesita hacer una vez)
        await NLP_Toolkit_IA.init();

        console.log("\n--- ANALIZANDO TEXTO ---");
        console.log("Texto Original:", textoDeEjemplo.trim());

        // Genera y muestra el resumen
        const resumen = await NLP_Toolkit_IA.summarize(textoDeEjemplo);
        console.log("\n✅ Resumen Generado:");
        console.log(resumen);

        // Extrae y muestra los conceptos clave
        const conceptos = await NLP_Toolkit_IA.extractKeyConcepts(textoDeEjemplo);
        console.log("\n🔑 Conceptos Clave Encontrados:");
        console.log(conceptos);

    } catch (error) {
        console.error("Ocurrió un error:", error);
    }
}

// Ejecuta la función principal
main();