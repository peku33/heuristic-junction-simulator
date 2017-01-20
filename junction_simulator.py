#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import random
import math

# Klasa pomocnicza
class TrafficDirections:
	DIRECTIONS_COUNT = 4
	PLANES_COUNT = 2

	# Płaszczyzny ruchu
	PLANE_UP_DOWN = 0
	PLANE_LEFT_RIGHT = 1

	# Pozycja określa miejsce samochodu na mapie skrzyżowania
	POSITION_UP = 0
	POSITION_DOWN = 1
	POSITION_LEFT = 2
	POSITION_RIGHT = 3

	# Kierunek oznacza w którą stronę samochód będzie skręcał, względem swojego toru jazdy
	DIRECTION_STRAIGHT = 100
	DIRECTION_TURN_LEFT = 101
	DIRECTION_TURN_RIGHT = 102

	@staticmethod
	def positionsToDirection(positionFrom, positionTo):
		if(positionFrom == positionTo):
			raise "positionFrom == positionTo"

		if(positionFrom == TrafficDirections.POSITION_UP):

			if(positionTo == TrafficDirections.POSITION_DOWN):
				return TrafficDirections.DIRECTION_STRAIGHT
			elif(positionTo == TrafficDirections.POSITION_LEFT):
				return TrafficDirections.DIRECTION_TURN_RIGHT
			elif(positionTo == TrafficDirections.POSITION_RIGHT):
				return TrafficDirections.DIRECTION_TURN_LEFT

		elif(positionFrom == TrafficDirections.POSITION_DOWN):

			if(positionTo == TrafficDirections.POSITION_UP):
				return TrafficDirections.DIRECTION_STRAIGHT
			elif(positionTo == TrafficDirections.POSITION_LEFT):
				return TrafficDirections.DIRECTION_TURN_LEFT
			elif(positionTo == TrafficDirections.POSITION_RIGHT):
				return TrafficDirections.DIRECTION_TURN_RIGHT

		elif(positionFrom == TrafficDirections.POSITION_LEFT):

			if(positionTo == TrafficDirections.POSITION_UP):
				return TrafficDirections.DIRECTION_TURN_LEFT
			elif(positionTo == TrafficDirections.POSITION_DOWN):
				return TrafficDirections.DIRECTION_TURN_RIGHT
			elif(positionTo == TrafficDirections.POSITION_RIGHT):
				return TrafficDirections.DIRECTION_STRAIGHT

		elif(positionFrom == TrafficDirections.POSITION_RIGHT):

			if(positionTo == TrafficDirections.POSITION_UP):
				return TrafficDirections.DIRECTION_TURN_RIGHT
			elif(positionTo == TrafficDirections.POSITION_DOWN):
				return TrafficDirections.DIRECTION_TURN_LEFT
			elif(positionTo == TrafficDirections.POSITION_LEFT):
				return TrafficDirections.DIRECTION_STRAIGHT


		raise "Invalid positionFrom / positionTo"

# Klasa reprezentująca jeden samochód na skrzyżowaniu
# addFrame		Numer ramki symulacji, w której samochód pojawił się na skrzyżowaniu
# leaveFrame	Numer ramki symulacji, w której samochów opuścił skrzyżowanie
# positionFrom	Numer kierunku (patrz TrafficDirections.POSITION_*) z którego przyjechał samochód
# positionsTo 	Numer kierunku (j/w) w którym chce pojechac samochód
class TrafficCar:
	def __init__(self, addFrame, leaveFrame, positionFrom, positionTo):
		self.addFrame = addFrame
		self.leaveFrame = leaveFrame
		self.positionFrom = positionFrom
		self.positionTo = positionTo

	# Przekalkolowuje pozycję źródłową i docelową, na kierunek skrętu, patrz TrafficDirections.DIRECTION_*
	def getDirection(self):
		return TrafficDirections.positionsToDirection(self.positionFrom, self.positionTo)

	def __repr__(self):
		return "Car, add: %d, leave: %d, from: %d, to: %d" % (self.addFrame, self.leaveFrame, self.positionFrom, self.positionTo)

# Klasa reprezentująca kolejkę samochodów czekających do skrzyżowania
# Skład się z dwóch składowych:
#	queuePre - kolejka samochodów stojących przed światłami
#	queuePost - kolejka samochodów, która minęła linię świateł. Ta kolejka ma ustaloną długośc, na queuePostLength. Puste miejsca są zaznaczone przez wartosc None
class TrafficQueue:

	def __init__(self, queuePostLength):
		self.queuePre = []
		self.queuePost = queuePostLength * [None]

	# Zwraca indeks pierwszego pustego elementu kolejki Post lub None, jeśli nie istnieje
	def postFindNoneIndex(self):
		for i, item in enumerate(self.queuePost):
			if item is None:
				return i

		return None

	# Zwraca, czy kolejka post jest pustya
	def postEmpty(self):
		for item in self.queuePost:
			if item is not None:
				return False
		return True

	# Czy kolejka jest całkowicie pusta?
	def isEmpty(self):
		return self.postEmpty() and not self.queuePre

	# Zwraca pierwszy samochód z kolejki Post
	def postPeekFirst(self):
		return self.queuePost[0]

	def postRemoveFirst(self):
		r = self.queuePost[0]
		self.queuePost[0] = None
		return r

	# Przesuwa kolejkę o jedno miejsce do przodu
	# Uzupełnia kolejkę Post wartościami kolejki Pre
	def tryPush(self, allowItemFromPre):
		noneIndex = self.postFindNoneIndex()				# Czy jest wolne miejsce na skrzyżowaniu?
		if noneIndex is None:								# Nie, nie przesuwamy
			return

		self.queuePost.pop(noneIndex)						# Tak, przesuwamy auta do przodu

		if allowItemFromPre and self.queuePre:				# Jeśli istnieją auta w kolejce pre - przenieś jedno z nich
			self.queuePost.append(self.queuePre.pop(0))
		else:
			self.queuePost.append(None)						# Jeśli nie - dodaj pusty element na końcu

	def append(self, item):
		self.queuePre.append(item)

	def __repr__(self):
		return "Post: %s || Pre: %s" % (self.queuePost, self.queuePre)

class TrafficSimulator:

	# Konstruktor wykonuje właściwą symulację.
	# trafficCarsPerSimulationMatrix		Tablica 4x4 przedstawiająca liczbę samochodów, która musi przejechac przez skrzyżowanie w każdym kierunku. Wiersze oznaczają kierunek źródłowy, kolumny - docelowy, w kolejności góra, dół, lewa, prawa
	# simulationCyclces						Liczba pełnych cykli świateł (zielone w jednej płaszczyźnie, okres martwy, zielone w drugiej płaszczyźnie, okres martwy) w trakcie jednej symulacji
	# lightsQueuePostSize					Liczba samochodów, jaka mieści się na skrzyżowaniu po przekroczeniu zielonego światła
	# simulationFramesPerLightCycle			Ile cykli ramek przypada na jeden cykl świateł. Samochody poruszają się o jeden krok na jedną ramkę
	# lightDutyCycles						Lista 4 współczynników (0.0 - 0.1) światła zielonego do całości cyklu, w kolejności: góra, dół, lewa, prawa

	# Uwaga! W trakcie jednego czasu martwego, przypadająca ilośc cykli (simulationFramesPerLightCycle - max(gora / dol) - max(lewo / prawo)) / 2 musi byc 2 razy wieksza niż pojemnośc skrzyzowania
	# Wynika to z faktu, że w pesymistycznym przypadku wszystkie samochody w jednym kierunku chca jechac w lewo a w drugim prosto.
	# W takim wypadku pierwsze lightsQueuePostSize cykli auta beda jechac prosto, a drugie lightsQueuePostSize beda skrecac w lewo.
	# Mniejsza wartośc moglaby doprowadzic do zapalenia sie zielonego przed zjadem samochodów ze skrzyżowania

	# trafficCarsPerSimulationMatrix zawiera *bezwględną* liczbę samochodów, która przejedzie przez skrzyżowanie w ciągu symulacji, pojawiając sie z równomiernym rozkładem
	# Ponieważ prędkośc ruchu samochodu jest stala i wynosi 1 / ramkę symulacji - parametr simulationFramesPerLightCycle mniej więcej definiuje szybkośc poruszania sie pojazdow i powinien byc staly
	# Parametr limitujacy liczbe samochodów na skrzyżowaniu - lightsQueuePostSize - powinien też byc staly - skrzyzowanie raczej sie nie powiekszy
	# lightDutyCycles - to główny parametr, który powinien by poddawany optymalizacji
	def __init__(self, trafficCarsPerSimulationMatrix, simulationCyclces, lightsQueuePostSize, simulationFramesPerLightCycle, lightDutyCycles):


		# self.simulationCyclces = simulationCyclces

		# Kolekcja samochodów, które opuściły skrzyżowanie
		self.removedCars = []

		# Liczba samochodów, jaka może stac "za swiatlami"
		lightsQueuePostEmpty = lightsQueuePostSize * [None]

		# Liczba ramek symulacji
		self.simulationFrames = simulationCyclces * simulationFramesPerLightCycle

		# Inicjalizacja kolejek
		trafficQueues = [TrafficQueue(lightsQueuePostSize), TrafficQueue(lightsQueuePostSize), TrafficQueue(lightsQueuePostSize), TrafficQueue(lightsQueuePostSize)]

		# Liczba cykli zielonego w każdym kierunku
		assert(len(lightDutyCycles) == TrafficDirections.DIRECTIONS_COUNT)

		lightSimulationFrames = TrafficDirections.DIRECTIONS_COUNT * [int]
		for i in range(0, TrafficDirections.DIRECTIONS_COUNT):
			assert(lightDutyCycles[i] < 1.0)
			lightSimulationFrames[i] = int(math.floor(lightDutyCycles[i] * simulationFramesPerLightCycle))
			assert(lightSimulationFrames[i] > 0)

		# Liczba cykli zielonego w każdej płaszczyźnie
		lightPlaneSimulationFrames = TrafficDirections.PLANES_COUNT * [int]
		lightPlaneSimulationFrames[TrafficDirections.PLANE_UP_DOWN] = max(lightSimulationFrames[TrafficDirections.POSITION_UP], lightSimulationFrames[TrafficDirections.POSITION_DOWN])
		lightPlaneSimulationFrames[TrafficDirections.PLANE_LEFT_RIGHT] = max(lightSimulationFrames[TrafficDirections.POSITION_LEFT], lightSimulationFrames[TrafficDirections.POSITION_RIGHT])

		# Liczba martwych cykli, pomiędzy zmianami płaszczyzny	
		lightDeadTimeFrames = (simulationFramesPerLightCycle - (lightPlaneSimulationFrames[TrafficDirections.PLANE_UP_DOWN] + lightPlaneSimulationFrames[TrafficDirections.PLANE_LEFT_RIGHT])) / 2

		# Sprawdź warunek, czy samochody na pewno zdążą opuścic skrzyżowanie
		if lightDeadTimeFrames < 2 * lightsQueuePostSize:
			raise Exception('lightDeadTimeFrames < 2 * lightsQueuePostSize')

		# Powtarzaj dopóki jest czas symulacji i skrzyżowanie nie jest puste
		self.simulationFrame = 0
		while self.simulationFrame < self.simulationFrames or not trafficQueues[0].isEmpty() or not trafficQueues[1].isEmpty() or not trafficQueues[2].isEmpty() or not trafficQueues[3].isEmpty():

			# Która ramka cyklu?
			lightCycleCurrent = self.simulationFrame % simulationFramesPerLightCycle


			# Ruch odbywa się po kolei, w cyklu:
			# 	Zielone Góra i/lub Dół
			#	DeadTime #1
			#	Zielone Lewo i/lub Prawo
			#	DeadTime

			# Czy obecny cykl to zielone w którąkolwiek stronę (True), czy DeadTime (False)
			cycleMove = None

			# Wartośc w każdym przypadku przesunięta od 0 do końca cyklu
			lightCycleCurrentOffset = lightCycleCurrent

			# Która para ? (Góra + Dół / Lewo + Prawo)
			cycleDirection1 = None
			cyclePositionThis2 = None

			# Która para nie?
			cycleDirectionOther1 = None
			cycleDirectionOther2 = None

			if lightCycleCurrent < lightPlaneSimulationFrames[TrafficDirections.PLANE_UP_DOWN]:																								# Zielone Góra i/lub Dół
				
				cycleMove = True
				lightCycleCurrentOffset = lightCycleCurrent

				cycleDirection1 = TrafficDirections.POSITION_UP
				cycleDirection2 = TrafficDirections.POSITION_DOWN

				cycleDirectionOther1 = TrafficDirections.POSITION_LEFT
				cycleDirectionOther2 = TrafficDirections.POSITION_RIGHT

			elif lightCycleCurrent < lightPlaneSimulationFrames[TrafficDirections.PLANE_UP_DOWN] + lightDeadTimeFrames: 																	# DeadTime #1

				cycleMove = False
				lightCycleCurrentOffset = lightCycleCurrent - (lightPlaneSimulationFrames[TrafficDirections.PLANE_UP_DOWN])

				cycleDirection1 = TrafficDirections.POSITION_UP
				cycleDirection2 = TrafficDirections.POSITION_DOWN

				cycleDirectionOther1 = TrafficDirections.POSITION_LEFT
				cycleDirectionOther2 = TrafficDirections.POSITION_RIGHT

			elif lightCycleCurrent < lightPlaneSimulationFrames[TrafficDirections.PLANE_UP_DOWN] + lightDeadTimeFrames + lightPlaneSimulationFrames[TrafficDirections.PLANE_LEFT_RIGHT]: 	# Zielone Lewo i/lub Prawo

				cycleMove = True
				lightCycleCurrentOffset = lightCycleCurrent - (lightPlaneSimulationFrames[TrafficDirections.PLANE_UP_DOWN] + lightDeadTimeFrames)

				cycleDirection1 = TrafficDirections.POSITION_LEFT
				cycleDirection2 = TrafficDirections.POSITION_RIGHT

				cycleDirectionOther1 = TrafficDirections.POSITION_UP
				cycleDirectionOther2 = TrafficDirections.POSITION_DOWN

			else:																																											# DeadTime #2

				cycleMove = False
				lightCycleCurrentOffset = lightCycleCurrent - (lightPlaneSimulationFrames[TrafficDirections.PLANE_UP_DOWN] + lightDeadTimeFrames + lightPlaneSimulationFrames[TrafficDirections.PLANE_LEFT_RIGHT])

				cycleDirection1 = TrafficDirections.POSITION_LEFT
				cycleDirection2 = TrafficDirections.POSITION_RIGHT

				cycleDirectionOther1 = TrafficDirections.POSITION_UP
				cycleDirectionOther2 = TrafficDirections.POSITION_DOWN

			########################################################################
			# Niezależnie od stanu świateł, samochody obecne na skrzyżowaniu,
			# próbują je opuścic. Samochodów w drugim kierunku w ogóle nie powinno
			# tu byc
			########################################################################

			# Sprawdz, czy na skrzyżowaniu nie zostały samochody z poprzednich kierunków.
			if (not trafficQueues[cycleDirectionOther1].postEmpty()) or (not trafficQueues[cycleDirectionOther2].postEmpty()):
				raise Exception('(not trafficQueues[cycleDirectionOther1].postEmpty()) or (not trafficQueues[cycleDirectionOther2].postEmpty())')

			# Sprawdź, czy na skrzyżowaniu, za światłami, stoją samochody.
			# Jeśli tak - sprawdź pierwszeństwo przejazdu
			cycleDirection1PostFirst = trafficQueues[cycleDirection1].postPeekFirst()
			cycleDirection2PostFirst = trafficQueues[cycleDirection2].postPeekFirst()

			# Na podstawie źródłowe i docelowej pozycji, oblicz kierunek skrętu
			cycleDirection1Direction = None
			if cycleDirection1PostFirst:
				cycleDirection1Direction = cycleDirection1PostFirst.getDirection()

			cycleDirection2Direction = None
			if cycleDirection2PostFirst:
				cycleDirection2Direction = cycleDirection2PostFirst.getDirection()

			# Blokada następuje tylko w przypadku, kiedy jeden samochód jedzie przez skrzyżowanie prosto (przejeżdża), a drugi skręca w lewo (czeka)
			# W każdym innym wypadku samochody przejeżdżają
			if not (cycleDirection1Direction == TrafficDirections.DIRECTION_STRAIGHT and cycleDirection2Direction == TrafficDirections.DIRECTION_TURN_LEFT):		# 1 jedzie, 2 czeka
				carMoved = trafficQueues[cycleDirection2].postRemoveFirst()
				if carMoved is not None:
					carMoved.leaveFrame = self.simulationFrame
					self.removedCars.append(carMoved)

			if not (cycleDirection2Direction == TrafficDirections.DIRECTION_STRAIGHT and cycleDirection1Direction == TrafficDirections.DIRECTION_TURN_LEFT):		# 2 jedzie, 1 czeka
				carMoved = trafficQueues[cycleDirection1].postRemoveFirst()
				if carMoved is not None:
					carMoved.leaveFrame = self.simulationFrame
					self.removedCars.append(carMoved)


			# Przesuń auta w kolejce.
			# Dodaj te z tyłu, jeśli jest zielone światło
			trafficQueues[cycleDirection1].tryPush(cycleMove and lightSimulationFrames[cycleDirection1] > lightCycleCurrentOffset)
			trafficQueues[cycleDirection2].tryPush(cycleMove and lightSimulationFrames[cycleDirection2] > lightCycleCurrentOffset)

			########################################################################
			# Generowanie nowych samochodów pojawiających się co ramkę
			########################################################################
			if(self.simulationFrame < self.simulationFrames):
				for positionFrom in range(0, TrafficDirections.DIRECTIONS_COUNT):			# Dla każdego kierunku z
					for positionTo in range(0, TrafficDirections.DIRECTIONS_COUNT):		# Dla każdego kierunku do
						if(positionFrom != positionTo):										# Pominięcie przekątnej
							if(
								trafficCarsPerSimulationMatrix[positionFrom][positionTo]	# Jeśli dostateczne prawdopodobieństwo pojawienia sie auta
								>
								random.uniform(0.0, self.simulationFrames)
							):
								trafficCar = TrafficCar(self.simulationFrame, None, positionFrom, positionTo) # Stwórz auto
								trafficQueues[positionFrom].append(trafficCar)

			self.simulationFrame = self.simulationFrame + 1

	# Oblicza sumaryczny czas (w ramkach) przez jaki samochody czekały na skrzyżowaniu
	def calculateSumWaitTime(self):
		sumWaitTime = 0

		for removedCar in self.removedCars:
			sumWaitTime += removedCar.leaveFrame - removedCar.addFrame

		return sumWaitTime

	# Znajduje najdłuższy czas (w ramkach) jaki którykolwiek z samochodów stał na skrzyżowaniu
	def calculateMaxWaitTime(self):
		maxWaitTime = 0

		for removedCar in self.removedCars:
			maxWaitTime = max(maxWaitTime, removedCar.leaveFrame - removedCar.addFrame)

		return maxWaitTime

	# Oblicza o ile ramek przedłużyła się symulacja, aby umożliwic zjazd wszystkim samochodom
	def getFramesOverrun(self):
		return self.simulationFrame - self.simulationFrames


# Przykładowe użycie
#
# 1. 1440 samochodów z każdego kierunku w każdy
#
# trafficCarsPerSimulationMatrix = [
# 	[0, 1440, 1440, 1440],
# 	[1440, 0, 1440, 1440],
# 	[1440, 1440, 0, 1440],
# 	[1440, 1440, 1440, 0],
# ]
# 
# -> Na skrzyżowaniu mieszcza się 3 samochody => opuszczenie skrzyżowania zajmuje 3 ramki
# -> Samochód opuszcza skrzyżowanie w 3 sekundy. 3 sekund = 3 ramek => 1 ramka = 1 sekunda
# -> Cykl świateł na skrzyżowaniu trwa 60 sekund. 2x2x3 sekundy to czas martwy = 12 sekund = 20% calosci czasu. Z tego wynika, że maksymalny duty cycle, w którąkolwiek stronę wynosi 0.80
# -> Sumulujemy 4 godziny. W tym czasie nastąpi 60 * 4 pełnych cykli
# 
# ts = TrafficSimulator(trafficCarsPerSimulationMatrix, 60 * 4, 3, 60, [0.4, 0.4, 0.4, 0.4])
# print(ts.calculateSumWaitTime())
# print(ts.calculateMaxWaitTime())
# print(ts.getFramesOverrun())