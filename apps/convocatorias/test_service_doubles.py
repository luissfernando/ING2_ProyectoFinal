"""Pruebas unitarias con dobles para el flujo de publicación.

El mock de Convocatoria representa el límite de persistencia (save) de la capa
de aplicación; las validaciones se sustituyen para probar cada rama del flujo.
"""
from unittest.mock import Mock, patch
from django.test import SimpleTestCase
from .models import (
    ESTADO_PENDIENTE,
    Convocatoria,
)
from .services import publicar
class ConvocatoriaEntityTests(SimpleTestCase):
    def test_etiqueta_transparencia_segun_porcentaje(self):
        convocatoria = Convocatoria(transparencia_pct=80)
        self.assertEqual(convocatoria.etiqueta_transparencia, "alta")
        convocatoria.transparencia_pct = 50
        self.assertEqual(convocatoria.etiqueta_transparencia, "media")
        convocatoria.transparencia_pct = 49
        self.assertEqual(convocatoria.etiqueta_transparencia, "baja")
    def test_medio_efectivo_prefiere_medio_postulacion_y_cae_a_email(self):
        convocatoria = Convocatoria(
            medio_postulacion="https://postula.unsa.edu.pe",
            email_contacto="rrhh@unsa.edu.pe",
        )
        self.assertEqual(
            convocatoria.medio_efectivo, "https://postula.unsa.edu.pe"
        )
        convocatoria.medio_postulacion = ""
        self.assertEqual(convocatoria.medio_efectivo, "rrhh@unsa.edu.pe")
class PublicarConDoblesTests(SimpleTestCase):
    @patch("apps.convocatorias.services.validar_legal", return_value=[])
    @patch("apps.convocatorias.services.faltantes_nivel_1", return_value=[])
    def test_publicacion_valida_actualiza_estado_y_guarda(self, _faltantes, _legal):
        convocatoria = Mock(spec=Convocatoria)
        convocatoria.recalcular_transparencia.return_value = 87

        errores = publicar(convocatoria)

        self.assertEqual(errores, [])
        self.assertEqual(convocatoria.estado, ESTADO_PENDIENTE)
        convocatoria.recalcular_transparencia.assert_called_once_with(guardar=False)
        convocatoria.save.assert_called_once_with()

    @patch(
        "apps.convocatorias.services.validar_legal",
        return_value=["La remuneración no cumple la regla legal."],
    )
    @patch("apps.convocatorias.services.faltantes_nivel_1", return_value=[])
    def test_publicacion_invalida_devuelve_errores_sin_persistir(
        self, _faltantes, _legal
    ):
        convocatoria = Mock(spec=Convocatoria)

        errores = publicar(convocatoria)

        self.assertEqual(errores, ["La remuneración no cumple la regla legal."])
        convocatoria.recalcular_transparencia.assert_not_called()
        convocatoria.save.assert_not_called()


class PublicarIntegracionRepositorioTests(SimpleTestCase):
    """Verifica el contrato entre publicar() y el método de persistencia save()."""

    @patch("apps.convocatorias.services.validar_legal", return_value=[])
    @patch("apps.convocatorias.services.faltantes_nivel_1", return_value=[])
    def test_publica_y_persiste_estado_pendiente(self, _faltantes, _legal):
        convocatoria = Mock(spec=Convocatoria)
        convocatoria.recalcular_transparencia.return_value = 75

        publicar(convocatoria)

        self.assertEqual(convocatoria.estado, ESTADO_PENDIENTE)
        convocatoria.save.assert_called_once_with()

