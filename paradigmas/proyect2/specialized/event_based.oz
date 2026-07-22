declare
  % Un bucle de eventos que espera mensajes (eventos) en un port
  proc {EventLoop EventPort}
    io:format("Bucle de eventos iniciado, esperando...~n", [])
    proc {Loop}
      case {Port.receive EventPort}
      of {buttonClick Id} then
        io:format("Evento: Botón '~s' clickeado.~n", [Id])
        {Loop}
      of {networkData Data} then
        io:format("Evento: Datos de red recibidos: '~s'~n", [Data])
        {Loop}
      of quit then
        io:format("Evento: Recibido 'quit', terminando bucle.~n", [])
      else
        io:format("Evento: Tipo desconocido recibido.~n", [])
        {Loop}
      end
    end
  in
    {Loop}
  end

in
  {NewPort SendEventPort ReceiveEventPort}
  thread {EventLoop ReceiveEventPort} end

  % Simulación de eventos
  {Delay 100}
  {SendEventPort buttonClick("Guardar")}
  {Delay 100}
  {SendEventPort networkData("{\"status\":\"ok\"}")}
  {Delay 100}
  {SendEventPort buttonClick("Cancelar")}
  {Delay 100}
  {SendEventPort quit}
