import calendar
from collections import Counter
from datetime import timedelta

from django.db.models import Avg

from .models import DesarrolloNino, SeguimientoDiario
from core.models import Asistencia
from novedades.models import Novedad


class GeneradorEvaluacionMensual:
    """
    Servicio para generar automáticamente el informe de desarrollo mensual de un niño.
    """

    def __init__(self, evaluacion_instance: DesarrolloNino):
        self.evaluacion = evaluacion_instance
        self.nino = self.evaluacion.nino
        self.fecha_fin_mes = self.evaluacion.fecha_fin_mes
        self.fecha_inicio_mes = self.fecha_fin_mes.replace(day=1)

        # Obtenemos los datos del mes una sola vez
        self.seguimientos_mes = self._get_seguimientos()
        self.novedades_mes = self._get_novedades()

    def run(self, only_tendencia=False, save_instance=True):
        """
        Ejecuta todos los pasos para generar y guardar la evaluación.
        Si only_tendencia=True, solo recalcula la tendencia respecto al mes anterior.
        Si save_instance=False, solo ejecuta la lógica pero no guarda el objeto.
        """
        if only_tendencia:
            self._generar_valoracion_general(only_asistencia=True)  # Solo asistencia
            if save_instance:
                self.evaluacion.save(run_generator=False) # Guardar sin volver a llamar al generador
            return
        self._generar_valoracion_general()
        self._generar_evaluacion_por_areas()
        self._generar_fortalezas()
        self._generar_aspectos_a_mejorar()
        self._generar_alertas()
        self._generar_conclusion_general()
        if save_instance:
            self.evaluacion.save(run_generator=False) # Guardar sin volver a llamar al generador

    def _get_seguimientos(self):
        return SeguimientoDiario.objects.filter(
            nino=self.nino,
            fecha__gte=self.fecha_inicio_mes,
            fecha__lte=self.fecha_fin_mes
        )

    def _get_novedades(self):
        return Novedad.objects.filter(
            nino=self.nino,
            fecha__gte=self.fecha_inicio_mes,
            fecha__lte=self.fecha_fin_mes
        )

    def _get_asistencias(self):
        return Asistencia.objects.filter(
            nino=self.nino,
            fecha__gte=self.fecha_inicio_mes,
            fecha__lte=self.fecha_fin_mes
        )

    def _generar_valoracion_general(self, only_asistencia=False):
        if not self.seguimientos_mes.exists():
            self.evaluacion.logro_mes = None
            self.evaluacion.tendencia_valoracion = None
            self.evaluacion.participacion_frecuente = None
            self.evaluacion.comportamiento_frecuente = None
            self.evaluacion.porcentaje_asistencia = None
            return

        # 1. Logro del Mes (Cualitativo)
        valoraciones = list(self.seguimientos_mes.values_list('valoracion', flat=True))
        if valoraciones:
            promedio = sum([v for v in valoraciones if v is not None]) / max(len([v for v in valoraciones if v is not None]), 1)
            if promedio >= 4.5:
                self.evaluacion.logro_mes = 'Alto'
            elif promedio >= 3:
                self.evaluacion.logro_mes = 'Adecuado'
            else:
                self.evaluacion.logro_mes = 'En Proceso'
        else:
            self.evaluacion.logro_mes = 'En Proceso'

        # 2. Tendencia
        mes_anterior_fin = self.fecha_inicio_mes - timedelta(days=1)
        try:
            desarrollo_anterior = DesarrolloNino.objects.get(nino=self.nino, fecha_fin_mes=mes_anterior_fin)
            if desarrollo_anterior.logro_mes and self.evaluacion.logro_mes:
                if self.evaluacion.logro_mes == desarrollo_anterior.logro_mes:
                    self.evaluacion.tendencia_valoracion = 'Se Mantiene'
                elif self.evaluacion.logro_mes == 'Alto' and desarrollo_anterior.logro_mes != 'Alto':
                    self.evaluacion.tendencia_valoracion = 'Avanza'
                elif self.evaluacion.logro_mes == 'En Proceso' and desarrollo_anterior.logro_mes != 'En Proceso':
                    self.evaluacion.tendencia_valoracion = 'Retrocede'
                else:
                    self.evaluacion.tendencia_valoracion = 'Se Mantiene'
            else:
                self.evaluacion.tendencia_valoracion = 'Sin datos previos'
        except DesarrolloNino.DoesNotExist:
            self.evaluacion.tendencia_valoracion = 'Sin datos previos'

        # 3. Participación y Comportamiento más frecuentes
        comportamientos = list(self.seguimientos_mes.values_list('comportamiento_general', flat=True))
        if comportamientos:
            from collections import Counter
            conteo = Counter(comportamientos)
            mas_frecuente = conteo.most_common(1)[0][0]
            self.evaluacion.comportamiento_frecuente = mas_frecuente
            # Si el comportamiento más frecuente es participativo, lo reflejamos en participación
            if mas_frecuente == 'participativo':
                self.evaluacion.participacion_frecuente = 'Alta'
            elif mas_frecuente == 'colaborativo':
                self.evaluacion.participacion_frecuente = 'Media'
            else:
                self.evaluacion.participacion_frecuente = 'Baja'
        else:
            self.evaluacion.comportamiento_frecuente = None
            self.evaluacion.participacion_frecuente = None

        # 4. Porcentaje de Asistencia
        asistencias_mes = self._get_asistencias()
        total_dias_registrados = asistencias_mes.count()
        dias_presente = asistencias_mes.filter(estado='Presente').count()
        if total_dias_registrados > 0:
            porcentaje = int((dias_presente / total_dias_registrados) * 100)
            self.evaluacion.porcentaje_asistencia = porcentaje
        else:
            self.evaluacion.porcentaje_asistencia = None

        if only_asistencia:
            return

    def _generar_evaluacion_por_areas(self):
        # Narrativo: integra observaciones relevantes con conectores y frases completas
        if not self.seguimientos_mes.exists():
            self.evaluacion.evaluacion_cognitiva = "No hay suficientes datos para una evaluación."
            self.evaluacion.evaluacion_comunicativa = "No hay suficientes datos para una evaluación."
            self.evaluacion.evaluacion_socio_afectiva = "No hay suficientes datos para una evaluación."
            self.evaluacion.evaluacion_corporal = "No hay suficientes datos para una evaluación."
            return

        dimensiones = {
            'evaluacion_cognitiva': 'Cognitiva',
            'evaluacion_comunicativa': 'Comunicativa',
            'evaluacion_socio_afectiva': 'Socio-afectiva',
            'evaluacion_corporal': 'Corporal',
        }
        from collections import Counter
        from desarrollo.models import EvaluacionDimension

        for campo, nombre in dimensiones.items():
            desempenos = []
            observaciones = []
            fechas = []
            seguimientos_ordenados = self.seguimientos_mes.order_by('fecha')
            for seguimiento in seguimientos_ordenados:
                for ev in getattr(seguimiento, 'evaluaciones_dimension', []).all():
                    if nombre.lower() in ev.dimension.nombre.lower():
                        desempenos.append(ev.desempeno)
                        if ev.observacion:
                            observaciones.append(ev.observacion)
            if not desempenos and not observaciones:
                texto_final = f"En el área {nombre}, no se registraron datos suficientes para una evaluación este mes."
                setattr(self.evaluacion, campo, texto_final)
                continue
            if desempenos:
                conteo = Counter(desempenos)
                desempeno_frecuente = conteo.most_common(1)[0][0]
            else:
                desempeno_frecuente = None
            # Narrativa de observaciones
            if observaciones:
                partes = []
                partes.append("Observaciones relevantes:")
                if len(observaciones) >= 1:
                    partes.append(f"Al inicio del mes: {observaciones[0]}")
                if len(observaciones) > 2:
                    partes.append(f"Durante el mes: {observaciones[1]}")
                if len(observaciones) > 1:
                    partes.append(f"Al finalizar el mes: {observaciones[-1]}")
                texto_obs = " ".join(partes)
                if len(observaciones) > 3:
                    texto_obs += " (Se muestran solo las observaciones más representativas.)"
                texto_final = f"En el área {nombre}, el niño/a tuvo un desempeño {desempeno_frecuente.lower()} durante el mes. {texto_obs}"
            else:
                if desempeno_frecuente:
                    texto_final = f"En el área {nombre}, el niño/a tuvo un desempeño {desempeno_frecuente.lower()} durante el mes."
                else:
                    texto_final = f"En el área {nombre}, no se registraron datos suficientes para una evaluación este mes."
            setattr(self.evaluacion, campo, texto_final)

    def _generar_fortalezas(self):
        # --- Análisis de Dimensiones ---
        desempenos_por_dimension = {
            'Cognitiva': [], 'Comunicativa': [], 'Socio-afectiva': [], 'Corporal': []
        }
        map_dimensiones = {
            'cognitiva': 'Cognitiva', 'comunicativa': 'Comunicativa', 
            'socio-afectiva': 'Socio-afectiva', 'corporal': 'Corporal'
        }
        for seguimiento in self.seguimientos_mes.prefetch_related('evaluaciones_dimension__dimension'):
            for ev in seguimiento.evaluaciones_dimension.all():
                for key_lower, name_title in map_dimensiones.items():
                    if key_lower in ev.dimension.nombre.lower():
                        desempenos_por_dimension[name_title].append(ev.desempeno)
                        break
        # --- Fin Análisis ---

        if not self.seguimientos_mes.exists():
            self.evaluacion.fortalezas_mes = "No hay datos para identificar fortalezas."
            return

        fortalezas = []

        # 1. Desempeño y Tendencia
        if self.evaluacion.logro_mes == 'Alto':
            fortalezas.append("Valoraciones generales consistentemente altas durante el mes.")
        if self.evaluacion.tendencia_valoracion == 'Avanza':
            fortalezas.append("Tendencia de avance clara en comparación con el mes anterior.")
        # Nueva fortaleza: Desempeño destacado en dimensiones específicas
        for dimension, desempenos in desempenos_por_dimension.items():
            if desempenos:
                conteo = Counter(desempenos)
                if conteo.get('alto', 0) >= len(desempenos) * 0.6:
                    fortalezas.append(f"Destacó en el área {dimension} por su desempeño alto durante el mes.")

        # 2. Comportamiento y Emociones
        if self.evaluacion.comportamiento_frecuente in ['participativo', 'colaborativo', 'excelente']:
            fortalezas.append(f"Comportamiento general positivo y constructivo ('{self.evaluacion.get_comportamiento_frecuente_display()}').")

        estados_emocionales = list(self.seguimientos_mes.values_list('estado_emocional', flat=True).exclude(estado_emocional__isnull=True))
        if estados_emocionales:
            estado_frecuente = Counter(estados_emocionales).most_common(1)[0][0]
            if estado_frecuente in ['alegre', 'tranquilo', 'motivado', 'curioso']:
                fortalezas.append(f"Estado emocional predominante positivo ('{estado_frecuente.capitalize()}').")

        # 3. Asistencia y Estabilidad
        if self.evaluacion.porcentaje_asistencia and self.evaluacion.porcentaje_asistencia >= 90:
            fortalezas.append(f"Excelente asistencia ({self.evaluacion.porcentaje_asistencia}%), demostrando constancia.")

        novedades_criticas = [n for n in self.novedades_mes.filter(tipo__in=['a', 'b']) if n.get_prioridad() >= 4]
        if not novedades_criticas:
            fortalezas.append("Ausencia de novedades de alta prioridad, indicando un mes estable.")

        self.evaluacion.fortalezas_mes = "- " + "\n- ".join(fortalezas) if fortalezas else "Se requiere más observación para definir fortalezas claras."

    def _generar_aspectos_a_mejorar(self):
        # --- Análisis de Dimensiones ---
        desempenos_por_dimension = {
            'Cognitiva': [], 'Comunicativa': [], 'Socio-afectiva': [], 'Corporal': []
        }
        map_dimensiones = {
            'cognitiva': 'Cognitiva', 'comunicativa': 'Comunicativa', 
            'socio-afectiva': 'Socio-afectiva', 'corporal': 'Corporal'
        }
        for seguimiento in self.seguimientos_mes.prefetch_related('evaluaciones_dimension__dimension'):
            for ev in seguimiento.evaluaciones_dimension.all():
                for key_lower, name_title in map_dimensiones.items():
                    if key_lower in ev.dimension.nombre.lower():
                        desempenos_por_dimension[name_title].append(ev.desempeno)
                        break
        # --- Fin Análisis ---

        if not self.seguimientos_mes.exists():
            self.evaluacion.aspectos_a_mejorar = "No hay datos para identificar aspectos a mejorar."
            return
        
        aspectos = []
        dimensiones_con_dificultad = []
        # 1. Dimensiones con bajo desempeño (si hay al menos un bajo/en proceso/requiere apoyo, se menciona)
        for dimension, desempenos in desempenos_por_dimension.items():
            if desempenos:
                conteo = Counter(desempenos)
                total = len(desempenos)
                bajos = conteo.get('bajo', 0) + conteo.get('requiere_apoyo', 0) + conteo.get('en_proceso', 0)
                if bajos > 0:
                    porcentaje_bajo = int((bajos/total)*100) if total else 0
                    dimensiones_con_dificultad.append(f"{dimension} ({porcentaje_bajo}% del mes con desempeño bajo o en proceso)")
        if dimensiones_con_dificultad:
            aspectos.append(
                "Se identifican áreas de oportunidad en las siguientes dimensiones: " + ", ".join(dimensiones_con_dificultad) + ". Es importante fortalecer el acompañamiento y las estrategias pedagógicas en estos aspectos para favorecer el desarrollo integral del niño/a."
            )
        # 2. Tendencia general
        if self.evaluacion.tendencia_valoracion == 'Retrocede':
            aspectos.append("Se observa un retroceso en el logro general en comparación con el mes anterior. Es crucial identificar las causas y reforzar el acompañamiento.")
        # 3. Valoraciones bajas globales
        valoraciones_bajas = self.seguimientos_mes.filter(valoracion__lte=2).count()
        if valoraciones_bajas > 2:
            aspectos.append(f"Se registraron {valoraciones_bajas} días con valoraciones bajas, lo que sugiere la necesidad de observar y dialogar sobre las situaciones presentadas en esas fechas.")
        # 4. Comportamiento y emociones
        if self.evaluacion.comportamiento_frecuente in ['retraido', 'dificultad', 'agresivo']:
            aspectos.append(f"El comportamiento más frecuente fue '{self.evaluacion.get_comportamiento_frecuente_display()}', lo que requiere atención y apoyo emocional.")
        estados_emocionales = list(self.seguimientos_mes.values_list('estado_emocional', flat=True).exclude(estado_emocional__isnull=True))
        if estados_emocionales:
            estado_frecuente = Counter(estados_emocionales).most_common(1)[0][0]
            if estado_frecuente in ['triste', 'irritable', 'ansioso', 'frustrado']:
                aspectos.append(f"El estado emocional predominante fue '{estado_frecuente.capitalize()}', por lo que se recomienda acompañamiento emocional y espacios de escucha.")
        # 5. Asistencia y novedades
        if self.evaluacion.porcentaje_asistencia and self.evaluacion.porcentaje_asistencia < 85:
            aspectos.append(f"El porcentaje de asistencia mensual ({self.evaluacion.porcentaje_asistencia}%) es bajo y puede afectar el proceso de desarrollo. Se sugiere buscar estrategias para mejorar la asistencia.")
        novedades_asistencia = self.novedades_mes.filter(tipo='c').count()
        if novedades_asistencia > 2:
            aspectos.append(f"Se registraron {novedades_asistencia} novedades por inasistencia, lo cual puede estar incidiendo en el proceso de adaptación y aprendizaje.")
        # 6. Novedades críticas
        novedades_criticas = [n for n in self.novedades_mes.filter(tipo__in=['a', 'b']) if n.get_prioridad() >= 4]
        if novedades_criticas:
            aspectos.append("Se presentaron novedades de alta prioridad (salud o emocional), por lo que se recomienda un seguimiento cercano y articulación con la familia.")
        self.evaluacion.aspectos_a_mejorar = "- " + "\n- ".join(aspectos) if aspectos else "No se identificaron aspectos críticos a mejorar este mes."

    def _generar_alertas(self):
        alertas = []

        # 1. Alerta por caída en el rendimiento general
        valoraciones = [s.valoracion for s in self.seguimientos_mes if s.valoracion is not None]
        if valoraciones:
            promedio_actual = sum(valoraciones) / len(valoraciones)
            mes_anterior_fin = self.fecha_inicio_mes - timedelta(days=1)
            mes_anterior_inicio = mes_anterior_fin.replace(day=1)
            seguimientos_anteriores = SeguimientoDiario.objects.filter(
                nino=self.nino, fecha__gte=mes_anterior_inicio, fecha__lte=mes_anterior_fin
            )
            valoraciones_anteriores = [s.valoracion for s in seguimientos_anteriores if s.valoracion is not None]

            if valoraciones_anteriores:
                promedio_anterior = sum(valoraciones_anteriores) / len(valoraciones_anteriores)
                # Se considera una caída significativa si el promedio baja más de 1.0 punto
                if promedio_actual < promedio_anterior - 1.0:
                    alertas.append(
                        f"Disminución del rendimiento: Se ha detectado una caída notable en el rendimiento general del niño/a este mes (promedio actual: {promedio_actual:.1f}, mes anterior: {promedio_anterior:.1f}). Se recomienda investigar las posibles causas."
                    )

        # 2. Alerta por estados emocionales negativos recurrentes
        estados_negativos = [
            s.estado_emocional for s in self.seguimientos_mes 
            if s.estado_emocional in ['triste', 'irritable', 'ansioso', 'frustrado', 'enojado']
        ]
        if len(estados_negativos) >= 4:  # Umbral de 4 o más días en el mes
            alertas.append(
                f"Estado emocional: Se han registrado estados emocionales negativos en {len(estados_negativos)} ocasiones durante el mes. Es importante ofrecer apoyo emocional y un espacio de diálogo."
            )

        # 3. Alerta por novedades críticas (salud, emocionales)
        novedades_criticas = [n for n in self.novedades_mes if n.tipo in ['a', 'b'] and n.get_prioridad() >= 4]
        if novedades_criticas:
            tipos = {}
            for nov in novedades_criticas:
                tipo = 'salud' if nov.tipo == 'a' else 'emocional'
                tipos[tipo] = tipos.get(tipo, 0) + 1
            
            for tipo, cantidad in tipos.items():
                plural = "novedad crítica" if cantidad == 1 else "novedades críticas"
                mensaje = f"Novedades de {tipo}: Se ha registrado {cantidad} {plural} de alta prioridad este mes. Se requiere seguimiento cercano y articulación con la familia."
                alertas.append(mensaje)

        # 4. Alerta por inasistencia crítica
        if self.evaluacion.porcentaje_asistencia is not None and self.evaluacion.porcentaje_asistencia < 70:
            alertas.append(f"Inasistencia crítica: El porcentaje de asistencia ({self.evaluacion.porcentaje_asistencia}%) es muy bajo y requiere una intervención inmediata para garantizar la continuidad del proceso pedagógico.")

        # 5. Alerta por comportamiento disruptivo frecuente
        comportamientos_negativos = self.seguimientos_mes.filter(comportamiento_general__in=['agresivo', 'dificultad']).count()
        if comportamientos_negativos >= 4:
            alertas.append(f"Comportamiento: Se observó un comportamiento disruptivo en {comportamientos_negativos} días, lo que sugiere la necesidad de implementar estrategias de manejo conductual y apoyo.")

        self.evaluacion.alertas_mes = "- " + "\n- ".join(alertas) if alertas else "No se generaron alertas automáticas este mes."

    def _generar_conclusion_general(self):
        if not self.seguimientos_mes.exists():
            self.evaluacion.conclusion_general = "No es posible generar una conclusión debido a la falta de seguimientos diarios este mes."
            return

        # --- 1. Recopilación de datos adicionales ---
        mes_nombre = calendar.month_name[self.fecha_fin_mes.month].capitalize()
        logro = self.evaluacion.logro_mes
        tendencia = self.evaluacion.tendencia_valoracion

        # Estado emocional más frecuente
        estados_emocionales = list(self.seguimientos_mes.values_list('estado_emocional', flat=True).exclude(estado_emocional__isnull=True))
        estado_emocional_frecuente = Counter(estados_emocionales).most_common(1)[0][0] if estados_emocionales else None

        # Observaciones relevantes del educador
        obs_relevantes = list(self.seguimientos_mes.filter(observacion_relevante=True).values_list('observaciones', flat=True))
        
        # Novedades críticas (salud/emocional)
        novedades_criticas = [n for n in self.novedades_mes.filter(tipo__in=['a', 'b']) if n.get_prioridad() >= 4]

        # --- 2. Construcción de la conclusión por partes ---
        partes_conclusion = []

        # Parte A: Desempeño general
        if logro == 'Alto':
            estado = f"mostró un desarrollo sobresaliente, cumpliendo consistentemente con los objetivos esperados."
        elif logro == 'Adecuado':
            estado = f"mostró un progreso constante y adecuado a su etapa de desarrollo."
        else: # En Proceso
            estado = f"se encontró en un proceso que requiere apoyo para afianzar los aprendizajes."
        partes_conclusion.append(f"Durante el mes de {mes_nombre}, el niño/a {estado}")

        # Parte B: Comportamiento y estado emocional
        if self.evaluacion.comportamiento_frecuente and estado_emocional_frecuente:
            # Mapeo para un lenguaje más natural
            map_emociones = {'alegre': 'alegría', 'tranquilo': 'tranquilidad', 'curioso': 'curiosidad', 'motivado': 'motivación'}
            emocion_texto = map_emociones.get(estado_emocional_frecuente, estado_emocional_frecuente)
            partes_conclusion.append(f"Su comportamiento predominante fue '{self.evaluacion.get_comportamiento_frecuente_display()}', manifestando principalmente un estado de {emocion_texto}.")

        # Parte C: Tendencia y observaciones clave
        if tendencia == 'Avanza':
            partes_conclusion.append("Se destaca una clara tendencia de avance respecto al mes anterior.")
        elif tendencia == 'Retrocede':
            partes_conclusion.append("Se observó un retroceso en su desempeño general, lo cual requiere atención.")

        if obs_relevantes:
            resumen_obs = ". ".join(obs_relevantes[:2]) # Tomamos las primeras 2 para ser concisos
            partes_conclusion.append(f"El educador destacó como observaciones relevantes: \"{resumen_obs}\".")

        # Parte D: Recomendación final basada en todo el contexto
        recomendacion = "La recomendación principal es continuar fomentando sus habilidades y mantener un seguimiento cercano a su proceso."
        if "No se identificaron aspectos críticos" not in self.evaluacion.aspectos_a_mejorar or novedades_criticas:
            recomendacion = "Se recomienda enfocar los esfuerzos en los 'aspectos a mejorar' identificados y atender las alertas generadas, trabajando en conjunto con la familia para establecer un plan de apoyo."
        partes_conclusion.append(recomendacion)

        # --- 3. Unión de las partes ---
        conclusion = " ".join(partes_conclusion)
        self.evaluacion.conclusion_general = conclusion
        if cantidad == 1:
                    alertas.append(f"Alerta: Se registró 1 novedad crítica de {tipo} este mes.")
        else:
                    alertas.append(f"Alerta: Se registraron {cantidad} novedades críticas de {tipo} este mes.")
        if self.evaluacion.porcentaje_asistencia is not None and self.evaluacion.porcentaje_asistencia < 70:
            alertas.append(f"Alerta de Inasistencia: El porcentaje de asistencia ({self.evaluacion.porcentaje_asistencia}%) es bajo y requiere atención.")
        self.evaluacion.alertas_mes = "\n".join(alertas) if alertas else "No se generaron alertas automáticas este mes."

    def _generar_conclusion_general(self):
        if not self.seguimientos_mes.exists():
            self.evaluacion.conclusion_general = "No es posible generar una conclusión debido a la falta de seguimientos diarios este mes."
            return

        # --- 1. Recopilación de datos adicionales ---
        mes_nombre = calendar.month_name[self.fecha_fin_mes.month].capitalize()
        logro = self.evaluacion.logro_mes
        tendencia = self.evaluacion.tendencia_valoracion

        # Estado emocional más frecuente
        estados_emocionales = list(self.seguimientos_mes.values_list('estado_emocional', flat=True).exclude(estado_emocional__isnull=True))
        estado_emocional_frecuente = Counter(estados_emocionales).most_common(1)[0][0] if estados_emocionales else None

        # Observaciones relevantes del educador
        obs_relevantes = list(self.seguimientos_mes.filter(observacion_relevante=True).values_list('observaciones', flat=True))
        
        # Novedades críticas (salud/emocional)
        novedades_criticas = [n for n in self.novedades_mes.filter(tipo__in=['a', 'b']) if n.get_prioridad() >= 4]

        # --- 2. Construcción de la conclusión por partes ---
        partes_conclusion = []

        # Parte A: Desempeño general
        if logro == 'Alto':
            estado = f"mostró un desarrollo sobresaliente, cumpliendo consistentemente con los objetivos esperados."
        elif logro == 'Adecuado':
            estado = f"mostró un progreso constante y adecuado a su etapa de desarrollo."
        else: # En Proceso
            estado = f"se encontró en un proceso que requiere apoyo para afianzar los aprendizajes."
        partes_conclusion.append(f"Durante el mes de {mes_nombre}, el niño/a {estado}")

        # Parte B: Comportamiento y estado emocional
        if self.evaluacion.comportamiento_frecuente and estado_emocional_frecuente:
            # Mapeo para un lenguaje más natural
            map_emociones = {'alegre': 'alegría', 'tranquilo': 'tranquilidad', 'curioso': 'curiosidad', 'motivado': 'motivación'}
            emocion_texto = map_emociones.get(estado_emocional_frecuente, estado_emocional_frecuente)
            partes_conclusion.append(f"Su comportamiento predominante fue '{self.evaluacion.get_comportamiento_frecuente_display()}', manifestando principalmente un estado de {emocion_texto}.")

        # Parte C: Tendencia y observaciones clave
        if tendencia == 'Avanza':
            partes_conclusion.append("Se destaca una clara tendencia de avance respecto al mes anterior.")
        elif tendencia == 'Retrocede':
            partes_conclusion.append("Se observó un retroceso en su desempeño general, lo cual requiere atención.")

        if obs_relevantes:
            resumen_obs = ". ".join(obs_relevantes[:2]) # Tomamos las primeras 2 para ser concisos
            partes_conclusion.append(f"El educador destacó como observaciones relevantes: \"{resumen_obs}\".")

        # Parte D: Recomendación final basada en todo el contexto
        recomendacion = "La recomendación principal es continuar fomentando sus habilidades y mantener un seguimiento cercano a su proceso."
        if "No se identificaron aspectos críticos" not in self.evaluacion.aspectos_a_mejorar or novedades_criticas:
            recomendacion = "Se recomienda enfocar los esfuerzos en los 'aspectos a mejorar' identificados y atender las alertas generadas, trabajando en conjunto con la familia para establecer un plan de apoyo."
        partes_conclusion.append(recomendacion)

        # --- 3. Unión de las partes ---
        conclusion = " ".join(partes_conclusion)
        self.evaluacion.conclusion_general = conclusion
        # Parte B: Comportamiento y estado emocional
        if self.evaluacion.comportamiento_frecuente and estado_emocional_frecuente:
            # Mapeo para un lenguaje más natural
            map_emociones = {'alegre': 'alegría', 'tranquilo': 'tranquilidad', 'curioso': 'curiosidad', 'motivado': 'motivación'}
            emocion_texto = map_emociones.get(estado_emocional_frecuente, estado_emocional_frecuente)
            partes_conclusion.append(f"Su comportamiento predominante fue '{self.evaluacion.get_comportamiento_frecuente_display()}', manifestando principalmente un estado de {emocion_texto}.")

        # Parte C: Tendencia y observaciones clave
        if tendencia == 'Avanza':
            partes_conclusion.append("Se destaca una clara tendencia de avance respecto al mes anterior.")
        elif tendencia == 'Retrocede':
            partes_conclusion.append("Se observó un retroceso en su desempeño general, lo cual requiere atención.")

        if obs_relevantes:
            resumen_obs = ". ".join(obs_relevantes[:2]) # Tomamos las primeras 2 para ser concisos
            partes_conclusion.append(f"El educador destacó como observaciones relevantes: \"{resumen_obs}\".")

        # Parte D: Recomendación final basada en todo el contexto
        recomendacion = "La recomendación principal es continuar fomentando sus habilidades y mantener un seguimiento cercano a su proceso."
        if "No se identificaron aspectos críticos" not in self.evaluacion.aspectos_a_mejorar or novedades_criticas:
            recomendacion = "Se recomienda enfocar los esfuerzos en los 'aspectos a mejorar' identificados y atender las alertas generadas, trabajando en conjunto con la familia para establecer un plan de apoyo."
        partes_conclusion.append(recomendacion)

        # --- 3. Unión de las partes ---
        conclusion = " ".join(partes_conclusion)
        self.evaluacion.conclusion_general = conclusion
        if cantidad == 1:
                    alertas.append(f"Alerta: Se registró 1 novedad crítica de {tipo} este mes.")
        else:
                    alertas.append(f"Alerta: Se registraron {cantidad} novedades críticas de {tipo} este mes.")
        if self.evaluacion.porcentaje_asistencia is not None and self.evaluacion.porcentaje_asistencia < 70:
            alertas.append(f"Alerta de Inasistencia: El porcentaje de asistencia ({self.evaluacion.porcentaje_asistencia}%) es bajo y requiere atención.")
        self.evaluacion.alertas_mes = "\n".join(alertas) if alertas else "No se generaron alertas automáticas este mes."

    def _generar_conclusion_general(self):
        if not self.seguimientos_mes.exists():
            self.evaluacion.conclusion_general = "No es posible generar una conclusión debido a la falta de seguimientos diarios este mes."
            return

        # --- 1. Recopilación de datos adicionales ---
        mes_nombre = calendar.month_name[self.fecha_fin_mes.month].capitalize()
        logro = self.evaluacion.logro_mes
        tendencia = self.evaluacion.tendencia_valoracion

        # Estado emocional más frecuente
        estados_emocionales = list(self.seguimientos_mes.values_list('estado_emocional', flat=True).exclude(estado_emocional__isnull=True))
        estado_emocional_frecuente = Counter(estados_emocionales).most_common(1)[0][0] if estados_emocionales else None

        # Observaciones relevantes del educador
        obs_relevantes = list(self.seguimientos_mes.filter(observacion_relevante=True).values_list('observaciones', flat=True))
        
        # Novedades críticas (salud/emocional)
        novedades_criticas = [n for n in self.novedades_mes.filter(tipo__in=['a', 'b']) if n.get_prioridad() >= 4]

        # --- 2. Construcción de la conclusión por partes ---
        partes_conclusion = []

        # Parte A: Desempeño general
        if logro == 'Alto':
            estado = f"mostró un desarrollo sobresaliente, cumpliendo consistentemente con los objetivos esperados."
        elif logro == 'Adecuado':
            estado = f"mostró un progreso constante y adecuado a su etapa de desarrollo."
        else: # En Proceso
            estado = f"se encontró en un proceso que requiere apoyo para afianzar los aprendizajes."
        partes_conclusion.append(f"Durante el mes de {mes_nombre}, el niño/a {estado}")

        # Parte B: Comportamiento y estado emocional
        if self.evaluacion.comportamiento_frecuente and estado_emocional_frecuente:
            # Mapeo para un lenguaje más natural
            map_emociones = {'alegre': 'alegría', 'tranquilo': 'tranquilidad', 'curioso': 'curiosidad', 'motivado': 'motivación'}
            emocion_texto = map_emociones.get(estado_emocional_frecuente, estado_emocional_frecuente)
            partes_conclusion.append(f"Su comportamiento predominante fue '{self.evaluacion.get_comportamiento_frecuente_display()}', manifestando principalmente un estado de {emocion_texto}.")

        # Parte C: Tendencia y observaciones clave
        if tendencia == 'Avanza':
            partes_conclusion.append("Se destaca una clara tendencia de avance respecto al mes anterior.")
        elif tendencia == 'Retrocede':
            partes_conclusion.append("Se observó un retroceso en su desempeño general, lo cual requiere atención.")

        if obs_relevantes:
            resumen_obs = ". ".join(obs_relevantes[:2]) # Tomamos las primeras 2 para ser concisos
            partes_conclusion.append(f"El educador destacó como observaciones relevantes: \"{resumen_obs}\".")

        # Parte D: Recomendación final basada en todo el contexto
        recomendacion = "La recomendación principal es continuar fomentando sus habilidades y mantener un seguimiento cercano a su proceso."
        if "No se identificaron aspectos críticos" not in self.evaluacion.aspectos_a_mejorar or novedades_criticas:
            recomendacion = "Se recomienda enfocar los esfuerzos en los 'aspectos a mejorar' identificados y atender las alertas generadas, trabajando en conjunto con la familia para establecer un plan de apoyo."
        partes_conclusion.append(recomendacion)

        # --- 3. Unión de las partes ---
        conclusion = " ".join(partes_conclusion)
        self.evaluacion.conclusion_general = conclusion
