declare
  % Contador mutable
  C = {NewCell 0} % Crea una celda con valor inicial 0

  proc {Increment}
    C := @C + 1  % Mutar el valor de la celda
  end

  proc {Decrement}
    C := @C - 1
  end

in
  {Increment}
  {Increment}
  {Browse @C} % Muestra 2 (dereferenciar la celda)
  {Decrement}
  {Browse @C} % Muestra 1
