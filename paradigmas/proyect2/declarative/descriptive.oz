declare
  % Representación de un documento HTML simple
  Document = html(head(title("Mi Página Oz"))
                  body([h1("Hola desde Oz")
                       p("Esto es un párrafo declarativo.")]))

  % Función para imprimir la estructura (para demostración)
  fun {PrintHtml Tree}
    case Tree
    of html(Head Body) then
      io:format("<html>~n", [])
      {PrintHtml Head}
      {PrintHtml Body}
      io:format("</html>~n", [])
    of head(Title) then
      io:format("<head>~n", [])
      {PrintHtml Title}
      io:format("</head>~n", [])
    of body(ContentList) then
      io:format("<body>~n", [])
      for Element in ContentList do
        {PrintHtml Element}
      end
      io:format("</body>~n", [])
    of title(Text) then
      io:format("<title>~s</title>~n", [Text])
    of h1(Text) then
      io:format("<h1>~s</h1>~n", [Text])
    of p(Text) then
      io:format("<p>~s</p>~n", [Text])
    end
  end

in
  {PrintHtml Document}
