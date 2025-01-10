# MMA Events

Data about upcoming events and recent mma decisions was scraped from great MMA portals https://mmadecisions.com and https://www.tapology.com

## Technologies used

1. Python with Flask framework
2. AWS RDS (as MySQL) and other AWS services
3. HTML / CSS / AJAX
4. Terraform for provisioning infra

## TO DO:

- Start using Gunicorn! Not just Flask.
- Move all scrapers to AWS Lambda
- Get token for RDS (MySQL) from Secret Manager (currently - variables in env)
- Refactor scrapers to check if event/bout/score exists in DB before inserting. Currently we have strange workarounds and unnecessary deletions
- Start collecting statistics for scrapers / web part.
- Add to Terraform: RDS, RDS subnet group, routing tables, routing associations, IGW, IGW attachment, DNS changes (in VPC settings and R53), also create new private RDS subnets, ECS cluster, ECS task definition, ECS service, ECS SG, ALB (target groups, etc), ACM certificate.
- "Dockerize" Web part and move to ECS? (EKS, somewhere else for learning purpose)
- Make RDS, ECS, ECR - private.
- Integrate with Elasticache for cache before MySQL? 