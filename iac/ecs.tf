module "ecs_cluster" {
  source  = "terraform-aws-modules/ecs/aws//modules/cluster"
  version = "~> 5.6"

  cluster_name = var.name

  fargate_capacity_providers = {
    FARGATE      = {}
    FARGATE_SPOT = {}
  }

  tags = var.tags
}

module "ecs_service" {
  source  = "terraform-aws-modules/ecs/aws//modules/service"
  version = "~> 5.6"

  name        = var.name
  cluster_arn = module.ecs_cluster.arn

  # supports external task def deployments
  # by ignoring changes to task definition and desired count
  ignore_task_definition_changes = true
  desired_count                  = 1

  # Task Definition
  enable_execute_command = false

  container_definitions = {
    (var.container_name) = {

      image = var.image

      port_mappings = [
        {
          protocol      = "tcp",
          containerPort = var.container_port
        }
      ]

      environment = [
        {
          "name" : "PORT",
          "value" : "${var.container_port}"
        },
        {
          "name" : "HEALTHCHECK",
          "value" : "${var.health_check}"
        },
        {
          "name" : "POSTGRES_DB"
          "value" : local.database_name
        },
        {
          "name" : "POSTGRES_HOST"
          "value" : module.aurora_postgres.cluster_endpoint
        },
        {
          "name" : "KNOWLEDGE_BASE_ID",
          "value" : aws_bedrockagent_knowledge_base.main.id
        },
        {
          "name" : "DB_SECRET_ARN",
          "value" : local.aurora_secret_arn
        },
      ]

      readonly_root_filesystem = false
    }
  }

  load_balancer = {
    service = {
      target_group_arn = module.alb.target_groups["ecs-task"].arn
      container_name   = var.container_name
      container_port   = var.container_port
    }
  }

  subnet_ids = module.vpc.private_subnets

  security_group_rules = {
    ingress_alb_service = {
      type                     = "ingress"
      from_port                = var.container_port
      to_port                  = var.container_port
      protocol                 = "tcp"
      description              = "Service port"
      source_security_group_id = module.alb.security_group_id
    }
    egress_all = {
      type        = "egress"
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  tasks_iam_role_name        = "${var.name}-tasks"
  tasks_iam_role_description = "role for ${var.name}"

  tasks_iam_role_statements = [
    {
      actions   = ["secretsmanager:GetSecretValue"]
      resources = [local.aurora_secret_arn]
    },
    {
      actions   = ["bedrock:Retrieve"]
      resources = ["arn:aws:bedrock:${local.region}:${local.account_id}:knowledge-base/*"]
    },
    {
      actions   = ["bedrock:InvokeModel"]
      resources = ["arn:aws:bedrock:${local.region}::foundation-model/*"]
    },
  ]

  tags = var.tags
}

module "alb" {
  source  = "terraform-aws-modules/alb/aws"
  version = "~> 9.0"

  name = var.name

  enable_deletion_protection = false

  vpc_id  = module.vpc.vpc_id
  subnets = module.vpc.public_subnets

  security_group_ingress_rules = {
    all_http = {
      from_port   = 80
      to_port     = 80
      ip_protocol = "tcp"
      description = "HTTP web traffic"
      cidr_ipv4   = "0.0.0.0/0"
    }
  }

  security_group_egress_rules = { for cidr_block in module.vpc.private_subnets_cidr_blocks :
    (cidr_block) => {
      ip_protocol = "-1"
      cidr_ipv4   = cidr_block
    }
  }

  listeners = {
    http = {
      port     = "80"
      protocol = "HTTP"

      forward = {
        target_group_key = "ecs-task"
      }
    }
  }

  target_groups = {

    ecs-task = {
      backend_protocol = "HTTP"
      backend_port     = var.container_port
      target_type      = "ip"

      health_check = {
        enabled             = true
        healthy_threshold   = 5
        interval            = 10
        matcher             = "200-299"
        path                = var.health_check
        port                = "traffic-port"
        protocol            = "HTTP"
        timeout             = 5
        unhealthy_threshold = 2
      }

      create_attachment = false
    }
  }

  tags = var.tags
}
