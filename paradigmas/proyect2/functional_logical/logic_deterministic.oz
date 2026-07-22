declare
  % Definición de un "predicado" para verificar si es un par (pattern matching)
  proc {IsEven N}
    case N
    of 0 then true
    of X when X > 0 then {IsOdd X-1}
    else false
    end
  end

  proc {IsOdd N}
    case N
    of 0 then false
    of X when X > 0 then {IsEven X-1}
    else false
    end
  end

  % Unificación de estructuras de datos (similar a Prolog)
  proc {HeadTail List Head Tail}
    List = Head|Tail
  end

in
  {Browse {IsEven 4}} % Muestra true
  {Browse {IsOdd 3}}  % Muestra true

  A = _ B = _ C = _
  {HeadTail [1 2 3] A B} % A se unifica con 1, B con [2 3]
  {Browse A} % Muestra 1
  {Browse B} % Muestra [2 3]
