"""Servicio (clase abstracta) y tres servicios especializados.

Polimorfismo: cada subclase sobrescribe ``describir``, ``validar_parametros`` y
``_tarifa_base``. Sobrecarga: ``calcular_costo`` admite varias variantes
(solo duración; con impuesto; con impuesto y descuento) mediante parámetros
opcionales, que es la forma idiomática de sobrecarga en Python.
"""

from abc import abstractmethod

from entidad import Entidad
from excepciones import (CalculoInconsistenteError, ParametroFaltanteError,
                         ServicioInvalidoError)

IVA = 0.19  # IVA colombiano por defecto


class Servicio(Entidad):
    """Clase abstracta para cualquier servicio que ofrece Software FJ."""

    def __init__(self, nombre: str, tarifa_hora: float, disponible: bool = True):
        super().__init__()
        if not nombre or not str(nombre).strip():
            raise ParametroFaltanteError("El servicio requiere un nombre.")
        if not isinstance(tarifa_hora, (int, float)) or tarifa_hora <= 0:
            raise ServicioInvalidoError("La tarifa por hora debe ser un número positivo.")
        self._nombre = str(nombre).strip()
        self._tarifa_hora = float(tarifa_hora)
        self._disponible = bool(disponible)

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def tarifa_hora(self) -> float:
        return self._tarifa_hora

    @property
    def disponible(self) -> bool:
        return self._disponible

    @disponible.setter
    def disponible(self, valor: bool) -> None:
        self._disponible = bool(valor)

    # --- métodos abstractos (se sobrescriben en cada subclase) ---
    @abstractmethod
    def validar_parametros(self, duracion: float) -> None:
        """Lanza ServicioInvalidoError si la duración no es válida para el servicio."""

    @abstractmethod
    def _tarifa_base(self) -> float:
        """Tarifa por hora efectiva, incluyendo recargos propios del servicio."""

    # --- método sobrecargado ---
    def calcular_costo(self, duracion: float, impuesto: float = 0.0,
                       descuento: float = 0.0) -> float:
        """Costo del servicio.

        Variantes:
            calcular_costo(2)             -> costo base
            calcular_costo(2, 0.19)       -> base + impuesto
            calcular_costo(2, 0.19, 0.10) -> (base - descuento) + impuesto
        """
        self.validar_parametros(duracion)
        if (not isinstance(impuesto, (int, float))
            
                or not isinstance(descuento, (int, float))):
            raise CalculoInconsistenteError("Impuesto y descuento deben ser numéricos.")
        if not 0 <= impuesto <= 1:
            raise CalculoInconsistenteError(f"Impuesto fuera de rango (0-1): {impuesto}")
        if not 0 <= descuento <= 1:
            raise CalculoInconsistenteError(f"Descuento fuera de rango (0-1): {descuento}")

        base = self._tarifa_base() * duracion
        neto = base * (1 - descuento)
        total = neto * (1 + impuesto)
        if total < 0 or total != total:  # negativo o NaN
            raise CalculoInconsistenteError("El costo calculado es inconsistente.")
        return round(total, 2)

    def describir(self) -> str:
        estado = "disponible" if self.disponible else "NO disponible"
        return (f"{self.__class__.__name__} #{self.id}: {self.nombre} "
                f"(${self.tarifa_hora:,.0f}/h, {estado})")


class ReservaSala(Servicio):
    """Reserva de salas: depende de la capacidad; duración entre 1 y 8 horas."""

    def __init__(self, nombre: str, tarifa_hora: float, capacidad: int,
                 disponible: bool = True):
        super().__init__(nombre, tarifa_hora, disponible)
        if not isinstance(capacidad, int) or capacidad <= 0:
            raise ServicioInvalidoError("La capacidad de la sala debe ser un entero positivo.")
        self._capacidad = capacidad

    def validar_parametros(self, duracion: float) -> None:
        if not isinstance(duracion, (int, float)) or not 1 <= duracion <= 8:
            raise ServicioInvalidoError("Una sala se reserva entre 1 y 8 horas.")

    def _tarifa_base(self) -> float:
        # Salas grandes (más de 20 personas) tienen 15 % de recargo.
        return self.tarifa_hora * (1.15 if self._capacidad > 20 else 1.0)

    def describir(self) -> str:
        return f"{super().describir()} | Sala para {self._capacidad} personas"


class AlquilerEquipo(Servicio):
    """Alquiler de equipos: cobra un depósito fijo y limita la duración a 72 h."""

    DEPOSITO = 20_000

    def __init__(self, nombre: str, tarifa_hora: float, tipo_equipo: str,
                 disponible: bool = True):
        super().__init__(nombre, tarifa_hora, disponible)
        if not tipo_equipo or not str(tipo_equipo).strip():
            raise ParametroFaltanteError("Debe indicar el tipo de equipo.")
        self._tipo_equipo = str(tipo_equipo).strip()

    def validar_parametros(self, duracion: float) -> None:
        if not isinstance(duracion, (int, float)) or not 1 <= duracion <= 72:
            raise ServicioInvalidoError("Un equipo se alquila entre 1 y 72 horas.")

    def _tarifa_base(self) -> float:
        return self.tarifa_hora

    def calcular_costo(self, duracion: float, impuesto: float = 0.0,
                       descuento: float = 0.0) -> float:
        # Sobrescritura: se suma el depósito al cálculo de la clase padre.
        return round(super().calcular_costo(duracion, impuesto, descuento)
                     + self.DEPOSITO, 2)

    def describir(self) -> str:
        return f"{super().describir()} | Equipo: {self._tipo_equipo}"


class AsesoriaEspecializada(Servicio):
    """Asesoría: se paga por hora de experto; mínimo 1 h, máximo 4 h."""

    NIVELES = {"junior": 1.0, "senior": 1.5, "experto": 2.0}

    def __init__(self, nombre: str, tarifa_hora: float, nivel: str = "junior",
                 disponible: bool = True):
        super().__init__(nombre, tarifa_hora, disponible)
        nivel = str(nivel).lower()
        if nivel not in self.NIVELES:
            raise ServicioInvalidoError(
                f"Nivel inválido {nivel!r}. Use: {', '.join(self.NIVELES)}.")
        self._nivel = nivel

    def validar_parametros(self, duracion: float) -> None:
        if not isinstance(duracion, (int, float)) or not 1 <= duracion <= 4:
            raise ServicioInvalidoError("Una asesoría dura entre 1 y 4 horas.")

    def _tarifa_base(self) -> float:
        return self.tarifa_hora * self.NIVELES[self._nivel]

    def describir(self) -> str:
        return f"{super().describir()} | Nivel: {self._nivel}"
