%%% NuevaHeredarDe.oz
%%% Generalización de HeredarDe para N superclases
%%% Sistema de objetos simplificado - Sección 7.6 CTM
%%% Raúl Andrés Alzate Gómez
%%%
%%% Requiere: Set.oz (Union, Inter, Minus) y Empacador.oz (NuevoEmpacador)
%%% insertados previamente via \insert

declare
Envolver Desenvolver
{NuevoEmpacador Envolver Desenvolver}

%%% NuevaHeredarDe: Generaliza HeredarDe para una lista de SuperClases
%%% {NuevaHeredarDe ClaseEmp SuperClasesEmp}
%%%   ClaseEmp: clase base empacada (mayor prioridad)
%%%   SuperClasesEmp: lista de superclases empacadas [S1 S2 ... Sn]
%%%     La última superclase en la lista tiene mayor prioridad entre superclases
%%% Valida que no existan conflictos de métodos ni atributos entre superclases
%%% que no sean resueltos por la clase base.

fun {NuevaHeredarDe ClaseEmp SuperClasesEmp}
   Clase = {Desenvolver ClaseEmp}
   SuperClases = {Map SuperClasesEmp Desenvolver}
   MA_Base = {Arity Clase.metodos}
   A_Base = Clase.atrbs

   proc {CheckPairwise S Rest}
      case Rest
      of nil then skip
      [] S2|Rr then
         MetConfl = {Minus {Inter {Arity S.metodos} {Arity S2.metodos}} MA_Base}
         AtrConfl = {Minus {Inter S.atrbs S2.atrbs} A_Base}
      in
         if MetConfl \= nil then
            raise herenciaIlegal(metEnConfl:MetConfl) end
         end
         if AtrConfl \= nil then
            raise herenciaIlegal(atrEnConfl:AtrConfl) end
         end
         {CheckPairwise S Rr}
      end
   end

   proc {ValidarPares Supers}
      case Supers
      of nil then skip
      [] _|nil then skip
      [] S|Sr then
         {CheckPairwise S Sr}
         {ValidarPares Sr}
      end
   end

   fun {MergeMethods Supers}
      case Supers
      of nil then m()
      [] [S] then S.metodos
      [] S|Sr then {Adjoin S.metodos {MergeMethods Sr}}
      end
   end

   fun {MergeAttrs Supers}
      case Supers
      of nil then nil
      [] [S] then S.atrbs
      [] S|Sr then {Union S.atrbs {MergeAttrs Sr}}
      end
   end

in
   {ValidarPares SuperClases}
   {Envolver c(metodos:{Adjoin {MergeMethods SuperClases} Clase.metodos}
               atrbs:{Union {MergeAttrs SuperClases} Clase.atrbs})}
end
