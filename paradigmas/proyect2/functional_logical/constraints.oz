declare
  [Space FD] = {Module.link ['x-oz://system/Space' 'x-oz://system/FD']}

  % Problema: Encontrar dos números X, Y tal que 1 <= X, Y <= 5, X+Y = 5 y X < Y
  proc {ConstraintExample X Y}
    local S in
      S = {Space.new}  % Crea un nuevo espacio de restricciones

      % Define los dominios de las variables
      X = {FD.var.lowerBound S 1}
      X = {FD.var.upperBound S 5}
      Y = {FD.var.lowerBound S 1}
      Y = {FD.var.upperBound S 5}

      % Añade las restricciones
      {FD.equal S X+Y 5}
      {FD.less S X Y}

      % Distribución (búsqueda de una solución)
      {Space.distribute S FD.value.max X}
      {Space.distribute S FD.value.max Y}
    end
  end

in
  XSolution = _ YSolution = _
  SolutionSpace = {Space.new}
  {ConstraintExample XSolution YSolution}
  {Browse XSolution#YSolution}
  % Muestra algo como 2#3 (si encuentra una solución)
