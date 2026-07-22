declare
  class ConcurrentCounter
    attr count
    meth init(InitialValue)
      self.count := InitialValue
    end
    meth increment(Step)
      % Esta operación es atómica para el objeto
      self.count := @self.count + Step
    end
    meth getCount($)
      @self.count
    end
  end

  proc {Worker Counter Id}
    for I in 1..1000 do
      {Counter increment(1)}
    end
    io:format("Worker ~s finished~n", [Id])
  end

in
  SharedCounter = {New ConcurrentCounter init(0)}
  thread {Worker SharedCounter "A"} end
  thread {Worker SharedCounter "B"} end
  thread {Worker SharedCounter "C"} end

  {Delay 500} % Espera un poco a que los hilos terminen
  {Browse {SharedCounter getCount($)}} % Debería mostrar 3000
