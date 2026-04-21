"""Shell completion scripts for agency."""

BASH_COMPLETION = """# bash completion for agency
_agency_completions()
{
    local cur prev words cword
    _init_completion || return

    case "${words[1]}" in
        init-project)
            _filedir
            ;;
        start)
            COMPREPLY=($(compgen -W "coder tester developer backend frontend devops" -- "${cur}"))
            _filedir
            ;;
        stop|resume|attach)
            COMPREPLY=($(compgen -W "$(agency list 2>/dev/null | grep "^agency-" | sed 's/agency-//')" -- "${cur}"))
            ;;
        tasks)
            case "${words[2]}" in
                add|assign|complete|approve|reject|reopen|update|show|delete)
                    ;;
                *)
                    COMPREPLY=($(compgen -W "list add show assign complete approve reject reopen update delete history" -- "${cur}"))
                    ;;
            esac
            ;;
        *)
            COMPREPLY=($(compgen -W "init-project start stop resume attach list tasks completions" -- "${cur}"))
            ;;
    esac
}

complete -F _agency_completions agency
"""

ZSH_COMPLETION = """# zsh completion for agency
_agency() {
    local -a commands
    commands=(
        "init-project:Create a new project"
        "start:Start an agent or manager"
        "stop:Stop a session"
        "resume:Resume a halted session"
        "attach:Attach to a session"
        "list:List sessions"
        "tasks:Task management"
        "completions:Print shell completion"
    )

    _arguments -C \\
        '1: :->command' \\
        '*: :->args'

    case "$state" in
        command)
            _describe 'command' commands
            ;;
        args)
            case "$words[1]" in
                init-project)
                    _arguments '*:directory:_files -/'
                    ;;
                start)
                    _arguments '1:agent:((coder tester developer backend frontend))' '*:directory:_files -/'
                    ;;
                stop|resume|attach)
                    _arguments '1:session:->session'
                    ;;
                tasks)
                    local -a task_commands
                    task_commands=(
                        "list:List tasks"
                        "add:Add task"
                        "show:Show task"
                        "assign:Assign task"
                        "complete:Complete task"
                        "approve:Approve task"
                        "reject:Reject task"
                        "reopen:Reopen task"
                        "update:Update task"
                        "delete:Delete task"
                        "history:Show history"
                    )
                    _describe 'task-command' task_commands
                    ;;
            esac
            ;;
    esac
}

compdef _agency agency
"""

FISH_COMPLETION = """# fish completion for agency
complete -c agency -n '__fish_use_subcommand' -a 'init-project' -d 'Create a new project'
complete -c agency -n '__fish_use_subcommand' -a 'start' -d 'Start an agent or manager'
complete -c agency -n '__fish_use_subcommand' -a 'stop' -d 'Stop a session'
complete -c agency -n '__fish_use_subcommand' -a 'resume' -d 'Resume a halted session'
complete -c agency -n '__fish_use_subcommand' -a 'attach' -d 'Attach to a session'
complete -c agency -n '__fish_use_subcommand' -a 'list' -d 'List sessions'
complete -c agency -n '__fish_use_subcommand' -a 'tasks' -d 'Task management'
complete -c agency -n '__fish_use_subcommand' -a 'completions' -d 'Print completion'

# Tasks subcommands
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'list' -d 'List tasks'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'add' -d 'Add task'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'show' -d 'Show task'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'assign' -d 'Assign task'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'complete' -d 'Complete task'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'approve' -d 'Approve task'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'reject' -d 'Reject task'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'reopen' -d 'Reopen task'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'update' -d 'Update task'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'delete' -d 'Delete task'
complete -c agency -n '__fish_seen_subcommand_from tasks' -a 'history' -d 'Show history'
"""


def get_completion_script(shell: str) -> str:
    """Get the completion script for a shell."""
    if shell == "bash":
        return BASH_COMPLETION
    elif shell == "zsh":
        return ZSH_COMPLETION
    elif shell == "fish":
        return FISH_COMPLETION
    else:
        raise ValueError(f"Unknown shell: {shell}")
