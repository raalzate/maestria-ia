@BUG-001
Feature: Bug fix for BUG-001 — la protopersona rompe personaje y el escenario no es comportamental

  Scenario: La fuga de identidad de IA se elimina de la respuesta
    Given una respuesta cruda del modelo que contiene "As a large language model, I need more information"
    When se sanea la respuesta del turno de simulación
    Then la frase de identidad de IA no aparece en el texto final
    And si no queda contenido útil se responde con una línea de recuperación en personaje

  Scenario: Cada turno local re-ancla la persona del escenario
    Given una sesión de chat local con sessionId activo y persona "Sofía Torres, Scrum Master"
    When el aprendiz envía un nuevo mensaje
    Then el mensaje enviado al modelo va prefijado con el ancla de personaje de la persona

  Scenario: El briefing de escena separa la misión del aprendiz del rol de la IA
    Given un escenario con situación activa cuyo framingDescription está dirigido al aprendiz
    When se construye el prompt de simulación
    Then el bloque de situación declara que la misión es del APRENDIZ y no de la persona
    And el bloque de objetivo exige hechos concretos y consistentes de la escena (equipo, sprint, tareas)

  Scenario: La configuración local por defecto favorece la adherencia
    Given la configuración por defecto del motor local
    Then el modelo por defecto es "gemma-e4b"
    And la temperatura de muestreo es menor o igual a 0.6
