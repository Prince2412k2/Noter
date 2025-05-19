path=$(pwd)
alias_cmd="alias note='python3 $path/main.py'"

# Check if alias is already defined in the current shell
if ! alias | grep -Fxq "$alias_cmd"; then
  echo "$alias_cmd" >>~/.bashrc
  echo "Alias added to .bashrc"
else
  echo "Alias already exists"
fi
