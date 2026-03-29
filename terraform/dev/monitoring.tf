# =============================================================================
# LumTrails Infrastructure - Cloud Monitoring and Alerting
# =============================================================================
# This file defines monitoring alerts for service health, errors, and 
# performance issues to enable proactive incident response.
# =============================================================================

# -----------------------------------------------------------------------------
# Notification Channel
# -----------------------------------------------------------------------------

resource "google_monitoring_notification_channel" "email" {
  display_name = "LumTrails Admin Email"
  type         = "email"
  project      = var.project_id
  
  labels = {
    email_address = var.alert_email
  }

  depends_on = [
    google_project_service.required_apis["monitoring.googleapis.com"]
  ]
}

# -----------------------------------------------------------------------------
# Main API Alerts
# -----------------------------------------------------------------------------

resource "google_monitoring_alert_policy" "main_api_error_rate" {
  count        = var.create_cloud_run_services ? 1 : 0
  display_name = "Main API High Error Rate"
  project      = var.project_id
  combiner     = "OR"
  
  conditions {
    display_name = "Error rate > 5%"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"lumtrails-api\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class=\"5xx\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.name]
  
  alert_strategy {
    auto_close = "1800s"
  }

  depends_on = [
    google_project_service.required_apis["monitoring.googleapis.com"],
    google_monitoring_notification_channel.email
  ]
}

resource "google_monitoring_alert_policy" "main_api_latency" {
  count        = var.create_cloud_run_services ? 1 : 0
  display_name = "Main API High Latency"
  project      = var.project_id
  combiner     = "OR"
  
  conditions {
    display_name = "P99 latency > 30s"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"lumtrails-api\" AND metric.type=\"run.googleapis.com/request_latencies\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 30000  # 30 seconds in ms
      
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_PERCENTILE_99"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.name]

  depends_on = [
    google_project_service.required_apis["monitoring.googleapis.com"],
    google_monitoring_notification_channel.email
  ]
}

# -----------------------------------------------------------------------------
# External API Alerts
# -----------------------------------------------------------------------------

resource "google_monitoring_alert_policy" "external_api_error_rate" {
  count        = var.create_cloud_run_services ? 1 : 0
  display_name = "External API High Error Rate"
  project      = var.project_id
  combiner     = "OR"
  
  conditions {
    display_name = "Error rate > 5%"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"lumtrails-external-api\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class=\"5xx\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.name]
  
  alert_strategy {
    auto_close = "1800s"
  }

  depends_on = [
    google_project_service.required_apis["monitoring.googleapis.com"],
    google_monitoring_notification_channel.email
  ]
}

# -----------------------------------------------------------------------------
# PDF Scanner Alerts (OOM and Long Processing)
# -----------------------------------------------------------------------------

resource "google_monitoring_alert_policy" "pdf_scanner_error_rate" {
  count        = var.create_cloud_run_services ? 1 : 0
  display_name = "PDF Scanner High Error Rate"
  project      = var.project_id
  combiner     = "OR"
  
  conditions {
    display_name = "Error rate > 10%"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"pdf-scan-worker\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class=\"5xx\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.1  # PDF scans can legitimately fail more often
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.name]
  
  alert_strategy {
    auto_close = "1800s"
  }

  depends_on = [
    google_project_service.required_apis["monitoring.googleapis.com"],
    google_monitoring_notification_channel.email
  ]
}

# -----------------------------------------------------------------------------
# Cloud Tasks Queue Depth Alert
# -----------------------------------------------------------------------------

resource "google_monitoring_alert_policy" "cloud_tasks_backlog" {
  count        = var.create_cloud_run_services ? 1 : 0
  display_name = "Cloud Tasks Queue Backlog"
  project      = var.project_id
  combiner     = "OR"
  
  conditions {
    display_name = "Queue depth > 100 tasks"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_tasks_queue\" AND metric.type=\"cloudtasks.googleapis.com/queue/depth\""
      duration        = "600s"  # 10 minutes
      comparison      = "COMPARISON_GT"
      threshold_value = 100
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.name]
  
  alert_strategy {
    auto_close = "1800s"
  }

  depends_on = [
    google_project_service.required_apis["monitoring.googleapis.com"],
    google_monitoring_notification_channel.email
  ]
}

# -----------------------------------------------------------------------------
# Cold Start Alert (for min_instances = 0 services)
# -----------------------------------------------------------------------------

resource "google_monitoring_alert_policy" "web_scanner_cold_starts" {
  count        = var.create_cloud_run_services ? 1 : 0
  display_name = "Web Scanner Frequent Cold Starts"
  project      = var.project_id
  combiner     = "OR"
  
  conditions {
    display_name = "Instance count frequently hitting 0"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"web-scan-worker\" AND metric.type=\"run.googleapis.com/container/instance_count\""
      duration        = "3600s"  # 1 hour
      comparison      = "COMPARISON_LT"
      threshold_value = 1
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.name]
  
  alert_strategy {
    auto_close = "3600s"
  }

  depends_on = [
    google_project_service.required_apis["monitoring.googleapis.com"],
    google_monitoring_notification_channel.email
  ]
}
