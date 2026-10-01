from sqlalchemy.orm import Session
from app.repositories.workload_repo import WorkloadRepository, OptimizationResultRepository
from app.engines.optimizer.workload_optimizer import generate_sample_workloads, optimize_workloads


class OptimizerService:
    def __init__(self, db: Session):
        self.db = db
        self.workload_repo = WorkloadRepository(db)
        self.result_repo = OptimizationResultRepository(db)

    def get_workloads(self):
        workloads = self.workload_repo.get_all()
        if not workloads:
            sample = generate_sample_workloads()
            for w in sample:
                self.workload_repo.create(w)
            workloads = self.workload_repo.get_all()
        return workloads

    def run_optimization(self):
        workloads = self.workload_repo.get_all()
        if not workloads:
            sample = generate_sample_workloads()
            for w in sample:
                self.workload_repo.create(w)
            workloads = self.workload_repo.get_all()

        workload_dicts = []
        for w in workloads:
            workload_dicts.append({
                "id": w.id,
                "workload_uuid": w.workload_uuid,
                "name": w.name,
                "workload_type": w.workload_type,
                "priority": w.priority,
                "is_security_critical": w.is_security_critical,
                "estimated_cpu_seconds": w.estimated_cpu_seconds,
                "estimated_memory_mb": w.estimated_memory_mb,
                "estimated_energy_kwh": w.estimated_energy_kwh,
                "estimated_co2_kg": w.estimated_co2_kg,
                "status": w.status,
                "scheduled_time": w.scheduled_time,
                "optimized_time": w.optimized_time,
            })

        result = optimize_workloads(workload_dicts)

        db_result = self.result_repo.create({
            "workloads_analyzed": result["workloads_analyzed"],
            "workloads_shifted": result["workloads_shifted"],
            "workloads_unchanged": result["workloads_unchanged"],
            "critical_protected": result["critical_protected"],
            "energy_before_kwh": result["energy_before_kwh"],
            "energy_after_kwh": result["energy_after_kwh"],
            "co2_before_kg": result["co2_before_kg"],
            "co2_after_kg": result["co2_after_kg"],
            "energy_saved_kwh": result["energy_saved_kwh"],
            "co2_saved_kg": result["co2_saved_kg"],
            "reduction_percentage": result["reduction_percentage"],
        })

        return {
            "result_id": db_result.id,
            "comparison": result,
        }

    def get_history(self):
        return self.result_repo.get_history(10)

    def get_comparison(self):
        latest = self.result_repo.get_latest()
        if not latest:
            return {"before": {}, "after": {}, "comparison": {}, "details": []}

        return {
            "before": {
                "energy_kwh": latest.energy_before_kwh,
                "co2_kg": latest.co2_before_kg,
            },
            "after": {
                "energy_kwh": latest.energy_after_kwh,
                "co2_kg": latest.co2_after_kg,
            },
            "comparison": {
                "energy_saved": latest.energy_saved_kwh,
                "co2_saved": latest.co2_saved_kg,
                "reduction_pct": latest.reduction_percentage,
            },
        }
