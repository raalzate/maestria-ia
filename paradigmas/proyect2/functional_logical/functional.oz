declare
  % Funcional de primer orden: Suma de elementos en una lista
  fun {SumList Xs}
    case Xs
    of nil then 0
    of X|Xr then X + {SumList Xr}
    end
  end

  % Funcional de alto orden: Map
  fun {Map F Xs}
    case Xs
    of nil then nil
    of X|Xr then {F X}|{Map F Xr}
    end
  end

  % Funcional de alto orden: FoldR
  fun {FoldR F Z Xs}
    case Xs
    of nil then Z
    of X|Xr then {F X {FoldR F Z Xr}}
    end
  end

in
  {Browse {SumList [1 2 3 4 5]}}  % Muestra 15

  % Ejemplo de Map: elevar al cuadrado
  {Browse {Map fun {$ X} X*X end [1 2 3]}} % Muestra [1 4 9]

  % Ejemplo de FoldR: sumar elementos (alternativa a SumList)
  {Browse {FoldR fun {$ X Y} X+Y end 0 [1 2 3 4 5]}} % Muestra 15
