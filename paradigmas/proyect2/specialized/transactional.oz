declare
  [Space] = {Module.link ['x-oz://system/Space']}

  % Un "recurso" que puede ser modificado transaccionalmente
  class BankAccount
    attr balance
    meth init(InitialBalance)
      self.balance := InitialBalance
    end
    meth getBalance($)
      @self.balance
    end
    meth deposit(Amount)
      self.balance := @self.balance + Amount
    end
    meth withdraw(Amount)
      if @self.balance >= Amount then
        self.balance := @self.balance - Amount
        true
      else
        false % Fondos insuficientes
      end
    end
  end

  % Simulación de una transacción
  proc {Transfer SourceAccount TargetAccount Amount}
    io:format("Intentando transferir ~s de ~s a ~s~n", [Amount SourceAccount TargetAccount])
    local S Res in
      S = {Space.new} % Nuevo espacio de transacción

      % Operaciones dentro de la transacción
      {S open}
      if {SourceAccount withdraw(Amount)} then
        {TargetAccount deposit(Amount)}
        Res = true
        {S commit} % Confirmar la transacción
        io:format("Transferencia exitosa: ~s~n", [Res])
      else
        Res = false
        {S abort}  % Abortar si no hay fondos
        io:format("Transferencia fallida: ~s (fondos insuficientes)~n", [Res])
      end
    end
    Res
  end

in
  AccountA = {New BankAccount init(100)}
  AccountB = {New BankAccount init(50)}

  {Browse {Transfer AccountA AccountB 30}} % Éxito
  {Browse {AccountA getBalance($)}} % Muestra 70
  {Browse {AccountB getBalance($)}} % Muestra 80

  {Browse {Transfer AccountA AccountB 80}} % Falla (fondos insuficientes en A)
  {Browse {AccountA getBalance($)}} % Sigue 70 (la transacción fallida no afecta)
  {Browse {AccountB getBalance($)}} % Sigue 80
