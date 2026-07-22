declare
  % Una clase para representar un agente con su propio comportamiento y comunicación
  class MultiAgent
    attr id name SendPort
    meth init(ID Name P)
      self.id := ID
      self.name := Name
      self.SendPort := P
      thread {self loop} end % Cada agente tiene su propio hilo
    end
    meth loop
      proc {ReceiveLoop}
        case {Port.receive @self.SendPort}
        of {message From Content} then
          io:format("Agente ~s (~s): Recibido '~s' de ~s~n", [@self.id @self.name Content From])
          % Aquí podría haber lógica de procesamiento y envío de respuesta
          {ReceiveLoop}
        of stop then
          io:format("Agente ~s: Detenido.~n", [@self.id])
        end
      end
    in
      io:format("Agente ~s (~s) iniciado.~n", [@self.id @self.name])
      {ReceiveLoop}
    end
    meth sendMessage(TargetPort Content)
      {TargetPort message(@self.id Content)}
    end
    meth stop
      {@self.SendPort stop}
    end
  end

in
  {NewPort P1 P1R} {NewPort P2 P2R}

  Agent1 = {New MultiAgent init(1 "Alpha" P1R)}
  Agent2 = {New MultiAgent init(2 "Beta" P2R)}

  {Agent1 sendMessage(P2 "Hola Agente Beta")}
  {Agent2 sendMessage(P1 "Saludos Agente Alpha")}

  {Delay 500}
  {Agent1 stop}
  {Agent2 stop}
