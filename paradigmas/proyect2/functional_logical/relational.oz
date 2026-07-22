declare
  [Search] = {Module.link ['x-oz://system/Search']}

  % Encontrar todas las divisiones de una lista en dos sublistas
  proc {Partition Xs Ys Zs}
    case Xs
    of nil then
      Ys = nil
      Zs = nil
    of H|T then
      {Search.choice
       Partition(T Ys (H|Zs))  % H va a Zs
       Partition(T (H|Ys) Zs)  % H va a Ys
      }
    end
  end

in
  Result = {Search.base.all
            proc {$ Res}
              Xs = [1 2 3]
              Ys = _ Zs = _
            in
              {Partition Xs Ys Zs}
              Res = Ys#Zs  % Retorna un par de sublistas
            end}
  {Browse Result}
  % Puede mostrar algo como:
  % [[nil#[3 2 1]] [[1]#[3 2]] [[2]#[3 1]] [[1 2]#[3]] ... ]
