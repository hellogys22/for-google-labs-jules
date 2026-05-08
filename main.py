import argparse
import sys

from agents import research_agent, content_agent, post_agent, track_agent

def main():
    parser = argparse.ArgumentParser(description="AI Affiliate Agent System")
    parser.add_argument('--run', type=str, choices=['agent1', 'agent2', 'agent3', 'agent4'],
                        help='Specify which agent to run (agent1=research, agent2=content, agent3=post, agent4=track)')
    parser.add_argument('--dry-run', action='store_true', help='Run all agents but skip actual Instagram post')

    args = parser.parse_args()

    if args.run == 'agent1':
        research_agent.run_agent()
    elif args.run == 'agent2':
        content_agent.run_agent()
    elif args.run == 'agent3':
        post_agent.run_agent(dry_run=args.dry_run)
    elif args.run == 'agent4':
        track_agent.run_agent()
    else:
        # Run all sequentially
        print("Running all agents sequentially...")
        research_agent.run_agent()
        content_agent.run_agent()
        post_agent.run_agent(dry_run=args.dry_run)
        track_agent.run_agent()

if __name__ == "__main__":
    main()