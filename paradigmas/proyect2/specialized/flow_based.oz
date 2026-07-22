declare
  % Componente "Generador": Produce una secuencia de números
  proc {Generator OutputPort}
    for I in 1..5 do
      {OutputPort I}
      {Delay 50}
    end
    {OutputPort stop} % Señal para el final del flujo
  end

  % Componente "Filtro": Multiplica los números por 2
  proc {Filter InputPort OutputPort}
    proc {Loop}
      case {InputPort} % Espera un valor
      of stop then {OutputPort stop}
      of N then
        {OutputPort N*2}
        {Loop}
      end
    end
  in
    {Loop}
  end

  % Componente "Consumidor": Imprime los números recibidos
  proc {Consumer InputPort}
    proc {Loop}
      case {InputPort}
      of stop then io:format("Consumidor: Fin de flujo.~n", [])
      of N then
        io:format("Consumidor: Recibido ~s~n", [N])
        {Loop}
      end
    end
  in
    {Loop}
  end

in
  % Conexiones (variables de flujo de datos)
  P1 = _ P2 = _

  thread {Generator P1} end     % Generador -> P1
  thread {Filter P1 P2} end     % P1 -> Filtro -> P2
  thread {Consumer P2} end     % P2 -> Consumidor

  {Delay 1000} % Espera un poco para la ejecución
