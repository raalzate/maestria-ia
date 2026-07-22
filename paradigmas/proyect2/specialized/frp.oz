declare
  % Un "modelo" que expone variables de flujo de datos
  class ReactiveModel
    attr _X _Y _Sum
    meth init(InitialX InitialY)
      self._X = InitialX
      self._Y = InitialY
      % La suma se calcula reactivamente cuando X o Y cambian
      thread
        local X Y in
          X = @self._X % Obtiene la referencia a la variable de flujo
          Y = @self._Y
          % Cuando X o Y se enlazan a un nuevo valor, _Sum se recalcula
          {WaitAndGet X}; {WaitAndGet Y};
          self._Sum = X+Y
        end
      end
    end
    meth setX(NewX) self._X = NewX end
    meth setY(NewY) self._Y = NewY end
    meth getSum($) @self._Sum end
  end

  % Una función "reactiva" para observar y reaccionar
  proc {ObserveSum Model}
    thread
      local S in
        S = {Model getSum($)} % Obtiene la variable de flujo de la suma
        io:format("Observador: Suma actual: ~s~n", [S])
        {ObserveSum Model} % Continuar observando (si la suma puede cambiar)
      end
    end
  end

in
  MyModel = {New ReactiveModel init(10 20)}
  thread {ObserveSum MyModel} end

  {Delay 100}
  {MyModel setX(15)} % Cambia X, la suma debería actualizarse
  {Delay 100}
  {MyModel setY(25)} % Cambia Y, la suma debería actualizarse
  {Delay 100}
  {MyModel setX(5)}  % Otro cambio
  {Delay 100}
