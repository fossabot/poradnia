Users
======

Kategoria użytkowników
----------------------

Zidentyfikowano następujące kategorie użytkowników:

Zespół (``is_staff=True``):

* Prawnik – osoba o pełnym dostępie do wszystkich danych zgromadzonych w systemie,
* Obserwator – osoby o dostępie do wybranych spraw wyłącznie na potrzeby jej obserwacji np. na potrzeby samokształcenia zespołu, specjalnego monitoringu,
* Wsparcie – osoba (praktykant, ekspert zewnętrzny) o dostępie do wybranych spraw na potrzeby realizacji określonych zadań w niej np. przygotowania pisma, ale bez możliwości kierowania sprawy do klienta,
* Wsparcie - wsparcie z możliwością samozatwierdzenie pisma i skierowanie go do klienta.
 
Osoba zewnętrzna (``is_staff=False``):

* Klient – osoba o dostępie do własnych spraw na potrzeby archiwalne oraz sporządzania nowych podań.
Przez każdego w sprawie należy rozumieć osobę, która jest albo prawnikiem, albo w kontekście danej sprawy obserwatorem, praktykantem, klientem.

Patrz `Uprawnienia`_.


Models
-----
.. automodule:: users.models
    :members:

Views
-----
.. automodule:: users.views
    :members:

Forms
-----
.. automodule:: users.forms
    :members:
