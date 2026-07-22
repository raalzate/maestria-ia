%%% Formulas.oz
%%% Objetos evaluadores de fórmulas - Polimorfismo
%%% Clases: Variable, Constante, Suma, Diferencia, Producto, Potencia
%%% Raúl Andrés Alzate Gómez

declare

fun {Pow B E}
   if E == 0 then 1
   elseif E == 1 then B
   else B * {Pow B E-1}
   end
end

class Variable
   attr val
   meth inic(V)
      val := V
   end
   meth asg(V)
      val := V
   end
   meth evaluar(X)
      X = @val
   end
end

class Constante
   attr val
   meth inic(V)
      val := V
   end
   meth evaluar(X)
      X = @val
   end
end

class Suma
   attr e1 e2
   meth inic(E1 E2)
      e1 := E1
      e2 := E2
   end
   meth evaluar(X)
      X = {@e1 evaluar($)} + {@e2 evaluar($)}
   end
end

class Diferencia
   attr e1 e2
   meth inic(E1 E2)
      e1 := E1
      e2 := E2
   end
   meth evaluar(X)
      X = {@e1 evaluar($)} - {@e2 evaluar($)}
   end
end

class Producto
   attr e1 e2
   meth inic(E1 E2)
      e1 := E1
      e2 := E2
   end
   meth evaluar(X)
      X = {@e1 evaluar($)} * {@e2 evaluar($)}
   end
end

class Potencia
   attr base exp
   meth inic(B E)
      base := B
      exp := E
   end
   meth evaluar(X)
      X = {Pow {@base evaluar($)} @exp}
   end
end

%%% Prueba: fórmula 3x² - xy + y³

local
   VarX = {New Variable inic(0)}
   VarY = {New Variable inic(0)}

   ExprX2     = {New Potencia inic(VarX 2)}
   Expr3      = {New Constante inic(3)}
   Expr3X2    = {New Producto inic(Expr3 ExprX2)}
   ExprXY     = {New Producto inic(VarX VarY)}
   Expr3X2mXY = {New Diferencia inic(Expr3X2 ExprXY)}
   ExprY3     = {New Potencia inic(VarY 3)}
   Formula    = {New Suma inic(Expr3X2mXY ExprY3)}
in
   % x=7, y=23 => 3(49) - 161 + 12167 = 12153
   {VarX asg(7)}
   {VarY asg(23)}
   {Browse {Formula evaluar($)}}

   % x=5, y=8 => 75 - 40 + 512 = 547
   {VarX asg(5)}
   {VarY asg(8)}
   {Browse {Formula evaluar($)}}
end
