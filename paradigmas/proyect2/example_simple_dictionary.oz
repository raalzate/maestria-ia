%! comment: This program implements a simple dictionary using a list of records.

declare Diccionario %! comment: Declares a variable 'Diccionario' which will hold our dictionary.

proc {CrearDiccionario} %! comment: Defines a procedure to initialize the dictionary.
   Diccionario = nil %! comment: Initializes the dictionary as an empty list (nil).
end

proc {AgregarEntrada Diccionario Key Value} %! comment: Defines a procedure to add an entry to the dictionary.
   Diccionario = entrada(key:Key value:Value)|Diccionario %! comment: Adds a new entry as a record at the head of the list.
end

proc {BuscarEntrada Diccionario Key ?Value} %! comment: Defines a procedure to search for an entry in the dictionary.
   case Diccionario of nil then %! comment: Base case: If the dictionary is empty (nil),
      Value = 'No encontrado' %! comment: then the value is 'No encontrado'.
   [] entrada(key:K value:V)|Resto then %! comment: Recursive case: If the dictionary is not empty, it deconstructs the head (entry) and the rest of the list.
      if K == Key then %! comment: If the key of the current entry matches the search key,
         Value = V %! comment: then the value is found.
      else %! comment: Otherwise,
         {BuscarEntrada Resto Key ?Value} %! comment: recursively search in the rest of the list.
      end
   end
end

%%! comment: Usage example:
{CrearDiccionario} %! comment: Creates an empty dictionary.
{AgregarEntrada Diccionario 'manzana' 'apple'} %! comment: Adds 'manzana':'apple' to the dictionary.
{AgregarEntrada Diccionario 'casa' 'house'} %! comment: Adds 'casa':'house' to the dictionary.

declare Resultado %! comment: Declares a variable 'Resultado' to store the search result.
{BuscarEntrada Diccionario 'manzana' ?Resultado} %! comment: Searches for 'manzana' in the dictionary.
{Show Resultado} %! comment: Displays the result (should be 'apple').

{BuscarEntrada Diccionario 'perro' ?Resultado} %! comment: Searches for 'perro' (which is not in the dictionary).
{Show Resultado} %! comment: Displays the result (should be 'No encontrado').

{BuscarEntrada Diccionario 'perro' ?Resultado}
{Show Resultado}