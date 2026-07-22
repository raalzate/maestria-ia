declare
  % Un recurso compartido que múltiples hilos acceden y modifican
  class SharedResource
    attr data
    meth init(InitialData)
      self.data := InitialData
    end
    meth update(NewValue)
      % Las actualizaciones sobre 'self.data' son protegidas por el objeto
      self.data := NewValue
      io:format("Recurso: Datos actualizados a ~s~n", [NewValue])
    end
    meth read($)
      @self.data
    end
  end

  proc {Updater Id Resource Value}
    io:format("Updater ~s: Intentando actualizar a ~s~n", [Id Value])
    {Resource update(Value)}
    io:format("Updater ~s: Actualización completa.~n", [Id])
  end

in
  MyResource = {New SharedResource init("Inicio")}

  thread {Updater "A" MyResource "ValorA"} end
  thread {Updater "B" MyResource "ValorB"} end
  thread {Updater "C" MyResource "ValorC"} end

  {Delay 500} % Espera a que los hilos terminen
  {Browse {MyResource read($)}} % Mostrará el último valor escrito
