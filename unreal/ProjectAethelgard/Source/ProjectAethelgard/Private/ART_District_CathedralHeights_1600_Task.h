#pragma once
#include "CoreMinimal.h"
#include "StateTreeTaskBase.h"
#include "StateTreeTask_OFFER_SHELTER_AND_BREAD.generated.h"

USTRUCT(meta = (DisplayName = "Task OFFER_SHELTER_AND_BREAD"))
struct MYGAMEPROJECT_API FStateTreeTask_OFFER_SHELTER_AND_BREAD : public FStateTreeTaskBase
{
    GENERATED_BODY()
    virtual EStateTreeRunStatus EnterState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult& Transition) const override
    {
        return EStateTreeRunStatus::Running;
    }
};
