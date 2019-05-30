# norsent
Sommerprosjekt -> https://norsent.herokuapp.com/
Hvis nettsiden har vært inaktiv vil det ta litt tid før den starter igjen når man går inn på den.

INFO:

Dette er et sommerprosjekt jeg har jobbet med sommeren 2018. 

Hvordan fungerer det?: 
Bruker machinelearning til å analysere setninger som blir tweetet av det gitte emnet. Videre vil hver setning bli gitt en verdi fra -1 til 1. 
Her er -1 veldig negativt og 1 er veldig positivt. Herfra tas gjennomsnittet av tidligere verdier og gir en positiv eller negativ trend. 
Hosting på heroku med gratis bruker sover hver 30 min hvis den står inaktiv og dermed resette databasen, dette gjør at grafene kan være nesten tom for datapunkter.
