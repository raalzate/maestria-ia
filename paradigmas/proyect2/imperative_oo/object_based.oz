declare
  % Clase simple de contador (sin herencia)
  class Counter
    attr count
    meth init(InitialValue)
      self.count := InitialValue
    end
    meth increment
      self.count := @self.count + 1
    end
    meth getCount($)
      @self.count
    end
  end

in
  MyCounter = {New Counter init(0)} % Crea una instancia
  {MyCounter increment}
  {MyCounter increment}
  {Browse {MyCounter getCount($)}} % Muestra 2

  AnotherCounter = {New Counter init(10)}
  {AnotherCounter increment}
  {Browse {AnotherCounter getCount($)}} % Muestra 11
