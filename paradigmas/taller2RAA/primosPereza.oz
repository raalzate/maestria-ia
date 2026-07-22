% Ejercicio 8: Programacion perezosa - Primos con criba de Eratostenes
% primosPereza.oz

% -------------------------------------------------------
% a) Gen: genera perezosamente la lista infinita de enteros desde I
% -------------------------------------------------------
fun lazy {Gen I}
   I | {Gen I+1}
end

% -------------------------------------------------------
% b) Primes: lista infinita de primos usando criba de Eratostenes perezosa
%
% FilterLazy: version perezosa de Filter que filtra multiplos de P
% Sieve: aplica la criba recursivamente: el primer elemento es primo,
%        se filtra el resto eliminando sus multiplos y se criba lo que queda
% -------------------------------------------------------

fun lazy {FilterLazy Xs P}
   case Xs
   of X|Xr then
      if X mod P \= 0 then X | {FilterLazy Xr P}
      else {FilterLazy Xr P}
      end
   end
end

fun lazy {Sieve Xs}
   case Xs
   of X|Xr then
      X | {Sieve {FilterLazy Xr X}}
   end
end

fun {Primes}
   {Sieve {Gen 2}}
end

% -------------------------------------------------------
% c) ShowPrimes: muestra los primeros N primos
% -------------------------------------------------------

proc {ShowPrimes N}
   proc {ShowN Ps K}
      if K > 0 then
         case Ps
         of P|Pr then
            {Show P}
            {ShowN Pr K-1}
         end
      end
   end
in
   {ShowN {Primes} N}
end

% -------------------------------------------------------
% Prueba: mostrar los primeros 20 primos
% -------------------------------------------------------
{ShowPrimes 20}
