declare
% max.oz - Autor: Raul A. Alzate
% Reescritura procedimental de Max:
% cada fun se sustituye por proc con parametro de salida explicito ?Res

proc {Max L ?Result}
   proc {MaxAcc Remaining CurrentMax ?Res}
      case Remaining
      of nil then Res = CurrentMax
      [] H|T then
         if H > CurrentMax then {MaxAcc T H Res}
         else {MaxAcc T CurrentMax Res}
         end
      end
   end
in
   case L
   of nil then raise emptyList end
   [] H|T then {MaxAcc T H Result}
   end
end

local R in
   {Max [10 20 5 30 15] R}
   {Browse R}  % Esperado: 30
end
