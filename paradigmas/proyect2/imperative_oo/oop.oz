declare
  % Clase base: Shape
  class Shape
    attr name
    meth init(Name)
      self.name := Name
    end
    meth getName($)
      @self.name
    end
    meth getArea($)
      0 % Valor por defecto
    end
  end

  % Clase derivada: Square, hereda de Shape
  class Square inherit Shape
    attr side
    meth init(Name Side)
      {self init(Name)} % Llama al constructor de la clase padre
      self.side := Side
    end
    meth getArea($)
      @self.side * @self.side
    end
  end

  % Clase derivada: Circle, hereda de Shape
  class Circle inherit Shape
    attr radius
    meth init(Name Radius)
      {self init(Name)}
      self.radius := Radius
    end
    meth getArea($)
      3.14159 * @self.radius * @self.radius
    end
  end

in
  MyShape = {New Shape init("Generic")}
  {Browse {MyShape getArea($)}} % Muestra 0

  MySquare = {New Square init("Cuadrado1" 5)}
  {Browse {MySquare getName($)}} % Muestra "Cuadrado1"
  {Browse {MySquare getArea($)}} % Muestra 25

  MyCircle = {New Circle init("Circulo1" 3)}
  {Browse {MyCircle getArea($)}} % Muestra 28.27431
