# traffic_current_directions
#	macierz opisująca natężenie ruchu samochodów we wszystkich kierunkach.
#	Wiersze oznaczają kierunek z którego nadjeżdża samochód
#	Kolumny kierunek w którym pojedzie samochód
#	Przekątna jest zawsze zerowa - zawracanie nie jest możliwe
#	Wartość oznacza liczbę samochodów, które chcą przejechać w określonym kierunku (o tym, w jakim czasie decyduje kontekst użycia)
#	
#	Kolejność kierunków, (zaczynając od lewego, górnego rogu): 1 = up, 2 = down, 3 = left, 4 = right
#	Przykład użycia: cars_per_hour[move.source, move.destination]
#
# test.traffic_current_directions_names <- c("up", "down", "left", "right")
# test.traffic_current_directions <- matrix(
#	 c(
#		 0, 0, 0, 0,
#		 0, 0, 0, 0,
#		 0, 0, 0, 0,
#		 0, 0, 0, 0
#	 ),
#	 nrow = 4,
#	 ncol = 4,
#	 byrow = TRUE, # Dzięki temu inicjalizacja wchodzi 1:1 w docelową macierz
#	 dimnames = list(test.traffic_current_directions_names, test.traffic_current_directions_names)
# )


# Funkcja wykonująca pełną symulację ruchu na skrzyżowaniu
# Ruch na skrzyżowaniu odbywa się w jednostkach czasowych - ramkach (frames).
# W trakcie jednej ramki samochód stojący na krawędzi skrzyżowania może je opuścić (jadąc prosto lub w prawo), a stojący za nim samochód zająć jego miejsce
# Przyjmuje parametry opisujące ruch:
#	traffic_current_directions			Ilość samochodów, w ciągu czasu symulacji, która pojawi się na skrzyżowaniu z zamiarem pojechania [z, do]
#	simulation.cycles					Liczba cykli zmian świateł, jakie wykona symulacja
#	lights.cycle_frames					Czas pełnego cyklu zmiany świateł, w arbitralnych jednostkach
#	lights.duty_ratio					Współczynniki zapalenia się zielonego światła w 4 kierunkach
junction_simulate <- function(traffic_current_directions, simulation.cycles, lights.cycle_frames, lights.duty_ratio)
{
	# Stała, oznaczająca liczbę kierunków skrzyżowania
	directions_num <- 4
	
	# Liczba samochodów, która mieści się na skrzyżowaniu
	junction.queue.current.size <- 5
	
	# Dwie kolejki:
	# 	junction.queue.waiting		- zawiera listę samochodów stojących z każdego kierunku PRZED światłami
	#	junction.queue.current		- zawiera listę samochodów które przekroczyły światła w danymi kierunku
	
	junction.queue.waiting <- list()
	length(junction.queue.waiting) <- directions_num
	junction.queue.current <- list()
	length(junction.queue.current) <- directions_num
	
	
	########################################################################
	# Obliczanie liczby cykli zielonego w każdym kierunku
	########################################################################
	lights.frames <- vector()
	for(direction_num in 1:directions_num)
		lights.frames[direction_num] <- floor(lights.duty_ratio[direction_num] * lights.cycle_frames)
		
	########################################################################
	# Obliczanie liczby cykli zielonego w każdej płaszczyźnie oraz czasu
	# martwego
	########################################################################
	lights.frames.up_down 		= max(lights.frames[1], lights.frames[2])
	lights.frames.left_right	= max(lights.frames[3], lights.frames[4])
	lights.frames.dead			= floor((lights.cycle_frames - lights.frames.up_down - lights.frames.left_right) / 2) # Okres martwy występuje pomiędzy każdą zmianą, dlatego /2
	
	# Jeśli sumaryczny czas zielonego w górę i w dół przekracza 100% - błąd
	if(lights.frames.dead <= 0)
		stop("max(up, down) + max(left, right) > 100%");
	
	simulation.frames <- simulation.cycles * lights.cycle_frames 
	for(current_frame in 1:simulation.frames)
	{
		########################################################################
		# Obliczenie aktywnego kierunku ruchu (w którą stronę zielone światło)
		########################################################################
		
		# Numer ramki obecnego cyklu
		lights.cycle_frame <- (current_frame - 1) %% lights.cycle_frames
		
		if(lights.cycle_frame < lights.frames.up_down) # 0 ... lights.frames.up_down - auta jadą góra / dół
		{
			print(paste("Ramka #", lights.cycle_frame, " auta jada gora / dol"))
			
			# Jeśli na skrzyżowaniu znajdują się jeszcze samochody z lewej / prawej - błąd
			if(
				length(junction.queue.current[[3]]) > 0
				||
				length(junction.queue.current[[4]]) > 0
			)
				stop("left / right current queue not empty")
				
			# Dopchnij skrzyżowanie z obu kierunków
			if(
				length(junction.queue.current[[1]]) < junction.queue.current.size # Za światłami nie jest pełno
				&&
				length(junction.queue.waiting[[1]]) > 0 # Jest kogo dopchnąć
			)
			{
				print("Przenoszenie auta")
				element <- junction.queue.waiting[[1]][1]
				junction.queue.waiting[[1]] <- junction.queue.waiting[[1]][-1]
				junction.queue.current[[1]] <- c(junction.queue.current[[1]], element)
			}
				
			# Jeśli na skrzyżowaniu jest już pełna ilość samochodów - pierwszy z nich próbuje je opuścić
			if(length(junction.queue.current[[1]]) >= junction.queue.current.size)
			{
				
			}
			
		}
		else if(lights.cycle_frame < lights.frames.up_down + lights.frames.dead) # lights.frames.up_down ... lights.frames.up_down + lights.frames.dead - wszystko stoi
		{
			print(paste("Ramka #", lights.cycle_frame, " auta stoja #1"))
		}
		else if(lights.cycle_frame < lights.frames.up_down + lights.frames.dead + lights.frames.left_right ) # lights.frames.up_down + lights.frames.dead ... lights.frames.up_down + lights.frames.dead + lights.frames.left_right - auta jadą lewo / prawo
		{
			print(paste("Ramka #", lights.cycle_frame, " auta jada lewo / prawo"))
		}
		else # Wszystko stoi
		{
			print(paste("Ramka #", lights.cycle_frame, " auta stoja #2"))
		}
		
			
		########################################################################
		# Generowanie nowych samochodów pojawiających się co ramkę
		########################################################################
		
		# Wygenerowana losowa macierz prawdopodobieństw, porównana z macierzą prawdopodobieństw wygenerowania samochodu w każdej ramce pokazuje, w których kierunkach pojawiają się samochody w danej ramcje
		
		# Wygeneruj losową macierz
		traffic_distribution <- matrix(runif(directions_num * directions_num, min = 0.0, max = simulation.frames), directions_num, directions_num)
		
		# Porównaj macierze (TRUE oznacza pojawienie się samochodu w danym kierunku)
		traffic_new_cars <- traffic_distribution < traffic_current_directions
		
		# Dla każdego kierunku, w przypadku przekroczenia prawdopodobieństwa (traffic_current_directions[x,y] / simulation.frames) - dodaj samochód
		for(traffic_new_cars.row in 1:nrow(traffic_new_cars))
			for(traffic_new_cars.col in 1:ncol(traffic_new_cars))
			{
				# Czy element macierzy jest TRUE?
				if(!traffic_new_cars[traffic_new_cars.row, traffic_new_cars.col])
					next;
					
				print(paste("Nowy samochod z ", traffic_new_cars.row, " do ", traffic_new_cars.col))
				
				# Dodaj nowy samochód do kolejki
				car.new <- list(
					entry_frame = current_frame,
					target_direction = traffic_new_cars.col
				)
				
				junction.queue.waiting[[traffic_new_cars.row]] <- c(junction.queue.waiting[[traffic_new_cars.row]], car.new)
			}
	}
	
	print(junction.queue.waiting)
	
	return(0)
}

model.traffic_current_directions_names <- c("up", "down", "left", "right")
model.traffic_current_directions <- matrix(
	c(
		0, 5, 0, 0,
		0, 0, 0, 0,
		0, 0, 0, 0,
		0, 0, 0, 0
	),
	nrow = 4,
	ncol = 4,
	byrow = TRUE,
	dimnames = list(model.traffic_current_directions_names, model.traffic_current_directions_names)
)

model.simulation.frames <- 5
model.lights.cycle_frames <- 10
model.lights.duty_ratio <- c(0.4, 0.4, 0.4, 0.4)

print("== START ==")
junction_simulate(model.traffic_current_directions, model.simulation.frames, model.lights.cycle_frames, model.lights.duty_ratio)
print("== END ==")

