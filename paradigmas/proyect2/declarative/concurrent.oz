declare
  proc {Producer X}
    for I in 1..3 do
      X = I   % X se enlaza secuencialmente a cada valor
    end
    X = unit  % Marca el final del flujo (o lo que el consumidor espere)
  end

  proc {Consumer X}
    case X
    of unit then
      io:format("Consumidor: Fin de datos~n", [])
    else
      io:format("Consumidor: Recibido ~s~n", [X])
      {Consumer X}
    end
  end

  X = _     % Variable de flujo de datos sin enlazar inicialmente
in
  thread {Producer X} end
  thread {Consumer X} end
  {Delay 1000} % Espera un poco para que los hilos terminen
