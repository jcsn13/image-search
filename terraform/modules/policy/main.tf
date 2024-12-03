# Allow Specific Organization Policies at Project Level
resource "google_project_organization_policy" "allow_cloudfunctions_ingress" {
  project    = var.project_id
  constraint = "constraints/cloudfunctions.allowedIngressSettings"

  list_policy {
    allow {
      all = true 
    }
  }
}

resource "google_project_organization_policy" "allow_compute_require_os_login" {
  project    = var.project_id
  constraint = "constraints/compute.requireOsLogin"

  boolean_policy {
    enforced = false
  }
}

resource "google_project_organization_policy" "allow_compute_trusted_image_projects" {
  project    = var.project_id
  constraint = "constraints/compute.trustedImageProjects"

  list_policy {
    allow {
      all = true
    }
  }
}

resource "google_project_organization_policy" "allow_storage_uniform_bucket_level_access" {
  project    = var.project_id
  constraint = "constraints/storage.uniformBucketLevelAccess"

  boolean_policy {
    enforced = false
  }
}

resource "google_project_organization_policy" "allow_compute_vm_external_ip_access" {
  project    = var.project_id
  constraint = "constraints/compute.vmExternalIpAccess"

  list_policy {
    allow {
      all = true
    }
  }
}

resource "google_project_organization_policy" "allow_compute_require_shielded_vm" {
  project    = var.project_id
  constraint = "constraints/compute.requireShieldedVm"

  boolean_policy {
    enforced = false  
  }
}

resource "google_project_organization_policy" "allow_iam_allowed_policy_member_domains" {
  project    = var.project_id
  constraint = "constraints/iam.allowedPolicyMemberDomains"

  list_policy {
    allow {
      all = true
    }
  }
}

resource "google_project_organization_policy" "disable_ip_forwarding" {
  project    = var.project_id
  constraint = "constraints/compute.vmCanIpForward"

  list_policy {
    allow {
      all = true
    }
  }
}

resource "google_project_organization_policy" "restrictVpcPeering" {
  project    = var.project_id
  constraint = "constraints/compute.restrictVpcPeering"

  list_policy {
    allow {
      all = true
    }
  }
}

resource "google_project_organization_policy" "allow_cloudbuild_worker_pools" {
  project    = var.project_id
  constraint = "constraints/cloudbuild.allowedWorkerPools"

  list_policy {
    allow {
      all = true
    }
  }
}